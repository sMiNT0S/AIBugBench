#!/usr/bin/env python3
"""
validation.repo_audit_enhanced — Comprehensive, offline-first repository audit.

Migrated from the former root script; no compatibility wrapper retained (private project cleanup).

Highlights
- Zero network calls by default; uses stdlib + optional local tools (ruff,
    mypy, pytest, coverage, bandit, pip-audit).
- Optional .repoaudit.yml config: weights, thresholds, paths, tool commands.
- Merges ignore rules from .gitignore / .semgrepignore / .trufflehogignore +
    config entries.
- Static security lint: yaml.load (no Loader), subprocess(shell=True), pickle,
    requests.* w/out timeout or verify=False, eval / exec.
- CI review: parses .github/workflows/*.yml for matrix, tested OS/Python,
    missing permissions blocks, unpinned actions.
- Produces plain console summary + optional JSON (sub-metrics + suggestions).
- Exit codes: 0 ran; nonzero with --strict if below threshold or critical
    issues present.
- Friendly banner: prints "Running repo audit, this may take a while..." first.

Environment
    AIBB_TIMEOUT=25   # seconds per external call
"""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterable
import contextlib
import fnmatch
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

try:
    import tomllib  # py311+
except Exception:  # pragma: no cover - optional
    tomllib = None  # type: ignore
try:
    import yaml  # PyYAML
except Exception:  # pragma: no cover - optional
    yaml = None  # type: ignore

DEFAULT_TIMEOUT = float(os.environ.get("AIBB_TIMEOUT", "25"))

DEFAULT_WEIGHTS = {
    "Documentation": 15,
    "Structure & Community": 15,
    "Code Quality": 15,
    "Testing": 15,
    "Security": 15,
    "CI/CD & Automation": 15,
    "Reproducibility": 10,
}

DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    ".tox",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    "htmlcov",
    ".idea",
    ".vscode",
}

SKIP_DIRS = DEFAULT_SKIP_DIRS  # public test API

DEFAULT_TEXT_EXTS = (
    ".py",
    ".md",
    ".toml",
    ".yml",
    ".yaml",
    ".txt",
    ".json",
    ".ini",
    ".cfg",
    ".rst",
)
BINARY_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".lock",
    ".zip",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
}

SECRET_PATTERNS = [
    r"api[_\-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]",
    r"(secret|passwd|password)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]",
    r"authorization:\s*bearer\s+[A-Za-z0-9\._\-]{20,}",
    r"token\s*[:=]\s*['\"][A-Za-z0-9\._\-]{20,}['\"]",
]
SECRET_RE = re.compile("|".join(SECRET_PATTERNS), re.IGNORECASE)

PLACEHOLDER_RE = re.compile(
    r"(YOUR_|YOUR-?|REPLACE_THIS|demo|fake|test|example|sample|placeholder|xxx|yyy|zzz)",
    re.IGNORECASE,
)

REQUESTS_CALL_RE = re.compile(r"\brequests\.(get|post|patch|put|delete|head|options)\s*\(", re.I)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
log = logging.getLogger("repo_audit")


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:  # pragma: no cover - IO fallback
        return ""


def safe_yaml_load(text: str) -> Any:
    if yaml is None:
        return None
    try:
        return yaml.safe_load(text)
    except Exception:
        return None


def load_yaml_file(p: Path) -> Any:
    if yaml is None or not p.exists():
        return None
    try:
        return yaml.safe_load(read_text(p))
    except Exception:
        return None


def load_toml_file(p: Path) -> dict[str, Any]:
    if tomllib is None or not p.exists():
        return {}
    try:
        return tomllib.loads(read_text(p))  # type: ignore[arg-type]
    except Exception:
        return {}


def run_cmd(cmd: list[str], cwd: Path, timeout: float = DEFAULT_TIMEOUT) -> tuple[int, str, str]:
    allowed = {
        "ruff",
        "mypy",
        "pytest",
        "coverage",
        "bandit",
        "pip-audit",
        "black",
        "isort",
        "flake8",
    }
    if not cmd or cmd[0] not in allowed:
        return 1, "", f"Command not allowed: {cmd[0] if cmd else 'empty'}"
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", f"{cmd[0]} not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def collect_ignore_patterns(repo: Path) -> list[str]:
    patterns: list[str] = []
    for name in [".gitignore", ".semgrepignore", ".trufflehogignore"]:
        p = repo / name
        if p.exists():
            for line in read_text(p).splitlines():
                s = line.strip()
                if s and not s.startswith("#"):
                    patterns.append(s)
    return patterns


def load_sabotage_allowlist(root: Path) -> set[str]:
    notes = root / "SABOTAGE_NOTES.md"
    allow: set[str] = set()
    if not notes.exists():
        return allow
    pattern = re.compile(r"ALLOW:\s*([a-zA-Z0-9_]+)\s+in\s+(.+)", re.I)
    for line in read_text(notes).splitlines():
        m = pattern.search(line)
        if m:
            rule = m.group(1).strip().lower()
            path = m.group(2).strip()
            allow.add(f"{rule}|{path}")
    return allow


def should_skip(rel_path: str, patterns: Iterable[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(rel_path.replace("\\", "/"), pat):
            return True
    parts = rel_path.split("/")
    return any(part.startswith(".") and part not in {".", ".."} for part in parts)


def list_repo_files(root: Path, include_hidden_dirs: bool, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for cur_root, dirs, fnames in os.walk(root):
        cur = Path(cur_root)
        dirs[:] = [d for d in dirs if d not in DEFAULT_SKIP_DIRS or include_hidden_dirs]
        for fn in fnames:
            p = cur / fn
            if not p.is_file():
                continue
            rel = p.relative_to(root).as_posix()
            if should_skip(rel, patterns):
                continue
            files.append(p)
    return files


def approx_code_stats(py_files: list[Path]) -> dict[str, int]:
    lines = 0
    for f in py_files:
        with contextlib.suppress(Exception):
            lines += len(read_text(f).splitlines())
    return {"py_file_count": len(py_files), "py_line_count": lines}


def docstring_coverage(py_files: list[Path]) -> dict[str, Any]:
    total_defs = 0
    with_doc = 0
    for f in py_files:
        text = read_text(f) or ""
        try:
            node = ast.parse(text, filename=str(f))
        except Exception:
            node = None
        if not node:
            continue
        for ch in ast.walk(node):
            if isinstance(
                ch,
                ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
            ):
                total_defs += 1
                if ast.get_docstring(ch):
                    with_doc += 1
    ratio = (with_doc / total_defs) if total_defs else 0.0
    return {"defs": total_defs, "with_docstrings": with_doc, "ratio": round(ratio, 3)}


def extract_version_from_changelog(changelog: str) -> str | None:
    m = re.search(r"^##?\s*\[?v?(\d+\.\d+\.[\w\.-]+)\]?", changelog, flags=re.M)
    return m.group(1) if m else None


def requirements_info(root: Path) -> dict[str, Any]:
    req = root / "requirements.txt"
    info = {"exists": req.exists(), "pinned": 0, "total": 0, "lines": []}
    if not req.exists():
        return info
    for line in read_text(req).splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        info["total"] += 1
        if "==" in s:
            info["pinned"] += 1
        info["lines"].append(s)
    return info


def pyproject_info(root: Path) -> dict[str, Any]:
    p = root / "pyproject.toml"
    info = {"exists": p.exists(), "version": None, "python_requires": None, "dependencies": []}
    if not p.exists():
        return info
    data = load_toml_file(p)
    proj = data.get("project", {})
    info["version"] = proj.get("version")
    info["python_requires"] = proj.get("requires-python")
    info["dependencies"] = proj.get("dependencies", [])
    return info


def tests_info(root: Path) -> dict[str, Any]:
    tests = []
    for pat in ("tests", "test"):
        d = root / pat
        if d.exists():
            tests.extend([p for p in d.rglob("test_*.py") if p.is_file()])
            tests.extend([p for p in d.rglob("*_test.py") if p.is_file()])
    return {"count": len(tests), "paths": [str(p) for p in tests]}


def ci_info(root: Path) -> dict[str, Any]:
    wf_dir = root / ".github" / "workflows"
    details = {
        "exists": wf_dir.exists(),
        "workflows": [],
        "has_matrix": False,
        "tested_os": set(),
        "tested_py": set(),
        "missing_permissions": [],
        "unversioned_actions": [],
    }
    if not wf_dir.exists() or yaml is None:
        return details
    for wf in wf_dir.glob("*.y*ml"):
        details["workflows"].append(wf.name)
        doc = load_yaml_file(wf)
        if not isinstance(doc, dict):
            continue
        jobs = doc.get("jobs", {})
        for jname, job in jobs.items():
            if not isinstance(job, dict):
                continue
            if "permissions" not in job:
                details["missing_permissions"].append(f"{wf.name}:{jname}")
            strat = job.get("strategy", {})
            matrix = strat.get("matrix", {})
            if matrix:
                details["has_matrix"] = True
                os_list = matrix.get("os", []) or matrix.get("runner", [])
                py_list = matrix.get("python-version", [])
                if isinstance(os_list, list):
                    details["tested_os"].update([str(x).lower() for x in os_list])
                if isinstance(py_list, list):
                    details["tested_py"].update([str(x) for x in py_list])
            steps = job.get("steps", [])
            for st in steps:
                if isinstance(st, dict) and "uses" in st:
                    uses = str(st["uses"])
                    if "@" not in uses or uses.endswith("@master") or uses.endswith("@main"):
                        details["unversioned_actions"].append(f"{wf.name}:{uses}")
    return details


def py_security_lints(py_files: list[Path], allowlist: set[str] | None = None) -> list[str]:
    allowlist = allowlist or set()

    def waived(line: str) -> bool:
        s = (line or "").lower()
        return "# nosec" in s or "audit:ignore" in s

    def allowed(rule: str, file_path: Path) -> bool:
        key_suffix = file_path.as_posix()
        for item in allowlist:
            try:
                rule_key, path_pat = item.split("|", 1)
            except ValueError:
                continue
            if rule_key.strip().lower() != rule:
                continue
            pp = path_pat.strip()
            if key_suffix.endswith(pp) or pp in key_suffix:
                return True
        return False

    findings: list[str] = []
    for f in py_files:
        txt = read_text(f)
        if not txt:
            continue
        lines = txt.splitlines()
        try:
            tree = ast.parse(txt or "", filename=str(f))
        except Exception:
            tree = None
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = None
                if isinstance(func, ast.Attribute):
                    name = f"{getattr(func.value, 'id', '')}.{func.attr}"
                elif isinstance(func, ast.Name):
                    name = func.id
                src_line = ""
                if hasattr(node, "lineno") and 1 <= node.lineno <= len(lines):
                    src_line = lines[node.lineno - 1]
                if name in {"yaml.load"} and not (waived(src_line) or allowed("unsafe_yaml", f)):
                    has_loader = any(
                        isinstance(k, ast.keyword) and k.arg and "Loader" in k.arg
                        for k in node.keywords or []
                    )
                    if not has_loader:
                        findings.append(f"{f}: yaml.load without Loader")
                if (
                    name in {"subprocess.run", "subprocess.call", "subprocess.Popen"}
                    and not (waived(src_line) or allowed("subprocess_shell", f))
                ):
                    for kw in node.keywords or []:
                        if (
                            kw.arg == "shell"
                            and isinstance(kw.value, ast.Constant)
                            and kw.value.value is True
                        ):
                            findings.append(f"{f}: subprocess with shell=True")
                if (
                    name in {"pickle.load", "pickle.loads"}
                    and not (waived(src_line) or allowed("pickle", f))
                ):
                    findings.append(f"{f}: pickle usage detected")
                if name in {"eval", "exec"} and not (waived(src_line) or allowed("eval_exec", f)):
                    findings.append(f"{f}: {name} usage detected")
        for m in REQUESTS_CALL_RE.finditer(txt):
            line_start = txt.rfind("\n", 0, m.start()) + 1
            line_end = txt.find("\n", m.end())
            if line_end == -1:
                line_end = len(txt)
            line = txt[line_start:line_end]
            raw = line.replace(" ", "")
            if "timeout=" not in line and not (
                waived(line) or allowed("requests_no_timeout", f)
            ):
                findings.append(f"{f}: requests call without timeout")
            if "verify=False" in raw and not (
                waived(line) or allowed("requests_verify_false", f)
            ):
                findings.append(f"{f}: requests call with verify=False")
    return findings


def secret_scan(files: list[Path], allow_test_noise: bool = True, max_hits: int = 20) -> list[str]:
    hits: list[str] = []
    for p in files:
        if p.suffix.lower() in BINARY_EXTS:
            continue
        txt = read_text(p)
        if not txt:
            continue
        if len(txt) > 1_000_000:
            continue
        for m in SECRET_RE.finditer(txt):
            snippet = m.group(0)
            if PLACEHOLDER_RE.search(snippet):
                continue
            rel = p.as_posix().lower()
            if allow_test_noise and any(
                seg in rel
                for seg in ["tests/", "/tests/", "/fixtures/", "fixture", "sample", "example"]
            ):
                continue
            line_start = txt.rfind("\n", 0, m.start()) + 1
            line_end = txt.find("\n", m.end())
            if line_end == -1:
                line_end = len(txt)
            line = txt[line_start:line_end].lower()
            if any(
                tag in line
                for tag in [
                    "# nosec",
                    "# noqa",
                    "audit:ignore",
                    "not real",
                    "example only",
                    "mock",
                    "stub",
                ]
            ):
                continue
            hits.append(f"{p}:{snippet[:120]}")
            if len(hits) >= max_hits:
                return hits
    return hits


def list_files(root: Path, exts: tuple[str, ...], include_hidden_dirs: bool = False) -> list[Path]:
    if not exts:
        return []
    root = Path(root)
    results: list[Path] = []
    for cur_root, dirs, files in os.walk(root):
        cur = Path(cur_root)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            p = cur / fn
            if not p.is_file():
                continue
            rel_parts = p.relative_to(root).parts
            is_hidden = any(part.startswith('.') and part not in {'.', '..'} for part in rel_parts)
            if is_hidden and not include_hidden_dirs:
                continue
            if p.suffix.lower() in exts:
                results.append(p)
    return results


def logging_usage(py_files: list[Path]) -> bool:
    return any("import logging" in read_text(p) or "logging." in read_text(p) for p in py_files)


def score_repo(
    root: Path,
    config: dict[str, Any],
    disable_static_security: bool = False,
) -> dict[str, Any]:
    weights = config.get("weights", DEFAULT_WEIGHTS)
    patterns = collect_ignore_patterns(root) + config.get("skip_paths", [])
    include_hidden = bool(config.get("include_hidden_dirs", False))
    all_files = list_repo_files(root, include_hidden_dirs=include_hidden, patterns=patterns)
    text_files = [p for p in all_files if p.suffix.lower() in DEFAULT_TEXT_EXTS]
    py_files = [p for p in all_files if p.suffix.lower() == ".py"]
    code_stats = approx_code_stats(py_files)
    readme_p = root / "README.md"
    quickstart_p = root / "QUICKSTART.md"
    license_p = next((p for p in root.glob("LICENSE*")), None)
    changelog_p = root / "CHANGELOG.md"
    contributing_p = root / "CONTRIBUTING.md"
    coc_p = root / "CODE_OF_CONDUCT.md"
    security_md = root / "SECURITY.md"
    readme_text = read_text(readme_p) if readme_p.exists() else ""
    changelog_text = read_text(changelog_p) if changelog_p.exists() else ""
    pp = pyproject_info(root)
    version = extract_version_from_changelog(changelog_text) or pp.get("version")
    ci = ci_info(root)
    ruff_rc, _, _ = run_cmd(["ruff", "check", "."], root)
    mypy_rc, _, _ = run_cmd(["mypy", "."], root)
    pytest_rc, _, _ = run_cmd(["pytest", "-q"], root)
    cov_rc, cov_out, _ = run_cmd(["coverage", "report"], root)
    bandit_rc, _, _ = run_cmd(["bandit", "-q", "-r", "."], root, timeout=90.0)
    pa_rc, _, _ = run_cmd(["pip-audit", "-q"], root)
    allowlist = load_sabotage_allowlist(root)
    sec_text_findings = [] if disable_static_security else py_security_lints(py_files, allowlist)
    secrets = secret_scan(text_files, allow_test_noise=True)
    has_badges = bool(re.search(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", readme_text))
    has_oneliner = bool(readme_text.splitlines()[0].strip()) if readme_text else False
    has_faq = bool(re.search(r"##\s*Frequently Asked Questions", readme_text, re.I))
    s_doc = 0.0
    if readme_text:
        s_doc += 0.25
    if has_oneliner:
        s_doc += 0.10
    if has_badges:
        s_doc += 0.10
    if has_faq:
        s_doc += 0.05
    if quickstart_p.exists():
        s_doc += 0.20
    if changelog_p.exists():
        s_doc += 0.10
    if license_p:
        s_doc += 0.10
    if contributing_p.exists():
        s_doc += 0.05
    if coc_p.exists():
        s_doc += 0.05
    s_doc = min(s_doc, 1.0)
    issue_tpl = any((root / ".github" / "ISSUE_TEMPLATE").glob("*.md"))
    pr_tpl = (root / ".github" / "pull_request_template.md").exists()
    s_struct = 0.0
    if issue_tpl:
        s_struct += 0.25
    if pr_tpl:
        s_struct += 0.25
    if security_md.exists():
        s_struct += 0.20
    if contributing_p.exists():
        s_struct += 0.15
    if coc_p.exists():
        s_struct += 0.15
    s_struct = min(s_struct, 1.0)
    doc_cov = docstring_coverage(py_files)["ratio"]
    s_quality = 0.0
    if code_stats["py_file_count"] > 0:
        s_quality += 0.10
    if ruff_rc in (0, 1):
        s_quality += 0.40
    if mypy_rc in (0, 1):
        s_quality += 0.30
    s_quality += min(doc_cov * 0.4, 0.20)
    s_quality = min(s_quality, 1.0)
    tests = tests_info(root)
    s_tests = 0.0
    if tests["count"] > 0:
        s_tests += 0.40
    if pytest_rc == 0:
        s_tests += 0.40
    elif pytest_rc == 1:
        s_tests += 0.20
    elif pytest_rc == 5:
        s_tests += 0.10
    if cov_rc == 0 and re.search(r"\b\d+%", cov_out):
        s_tests += 0.20
    s_tests = min(s_tests, 1.0)
    s_security = 0.0
    if security_md.exists():
        s_security += 0.10
    if bandit_rc == 0:
        s_security += 0.30
    if pa_rc == 0:
        s_security += 0.30
    if not secrets:
        s_security += 0.30
    if sec_text_findings:
        s_security = max(0.0, s_security - 0.30)
    s_security = min(s_security, 1.0)
    s_ci = 0.0
    if ci["exists"]:
        s_ci += 0.30
    if ci["has_matrix"]:
        s_ci += 0.30
    if len(ci["tested_os"]) >= 3:
        s_ci += 0.20
    if len(ci["tested_py"]) >= 1:
        s_ci += 0.20
    if ci["missing_permissions"]:
        s_ci = max(0.0, s_ci - 0.10)
    if ci["unversioned_actions"]:
        s_ci = max(0.0, s_ci - 0.10)
    s_ci = min(s_ci, 1.0)
    req = requirements_info(root)
    s_repro = 0.0
    if pp["exists"]:
        s_repro += 0.40
    if pp.get("python_requires"):
        s_repro += 0.30
    if req["exists"]:
        s_repro += 0.10
        if req["total"] > 0:
            s_repro += 0.20 * (req["pinned"] / req["total"])
    s_repro = min(s_repro, 1.0)
    scores = {
        "Documentation": s_doc * weights["Documentation"],
        "Structure & Community": s_struct * weights["Structure & Community"],
        "Code Quality": s_quality * weights["Code Quality"],
        "Testing": s_tests * weights["Testing"],
        "Security": s_security * weights["Security"],
        "CI/CD & Automation": s_ci * weights["CI/CD & Automation"],
        "Reproducibility": s_repro * weights["Reproducibility"],
    }
    total = sum(scores.values())
    total_max = sum(weights.values())
    suggestions: list[str] = []
    if ruff_rc == 127:
        suggestions.append("Install ruff and add to CI (pipx install ruff); fail on nonzero.")
    if mypy_rc == 127:
        suggestions.append(
            "Install mypy and add to CI; configure mypy.ini with strict=False to start."
        )
    if pytest_rc in (127, 124):
        suggestions.append("Ensure pytest is installed and tests discoverable (tests/).")
    if cov_rc in (127, 124):
        suggestions.append(
            "Install coverage and run `coverage run -m pytest && coverage report` in CI."
        )
    if bandit_rc in (127, 124):
        suggestions.append("Install bandit; tune excludes and `# nosec` for intentional patterns.")
    if pa_rc in (127, 124):
        suggestions.append("Install pip-audit; pin/upgrade vulnerable dependencies.")
    if ci["missing_permissions"]:
        suggestions.append(
            "Add least-privilege `permissions:` to jobs: "
            f"{', '.join(ci['missing_permissions'][:5])}"
        )
    if ci["unversioned_actions"]:
        suggestions.append(
            f"Pin GitHub Actions to versions: {', '.join(ci['unversioned_actions'][:5])}"
        )
    if secrets:
        suggestions.append(
            "Remove or rotate secrets; add tests/fixtures to tool excludes; "
            "use place-holders in examples."
        )
    if sec_text_findings:
        suggestions.append(
            "Fix static security findings (yaml.safe_load, no shell=True, add "
            "requests timeouts, avoid pickle/eval)."
        )
    if not (root / "SECURITY.md").exists():
        suggestions.append("Add SECURITY.md with disclosure process.")
    details = {
        "version": version or "Not found",
        "py_files": code_stats["py_file_count"],
        "py_lines": code_stats["py_line_count"],
        "docstring_coverage": doc_cov,
        "tests_detected": tests["count"],
        "ci_details": {
            "workflows": ci["workflows"],
            "has_matrix": ci["has_matrix"],
            "tested_os": sorted(ci["tested_os"]),
            "tested_py": sorted(ci["tested_py"]),
            "missing_permissions": ci["missing_permissions"],
            "unversioned_actions": ci["unversioned_actions"],
        },
        "requirements": req,
        "pyproject": pp,
        "secret_hits_sample": secrets[:5],
        "static_security_findings": sec_text_findings[:10],
        "tools": {
            "ruff_rc": ruff_rc,
            "mypy_rc": mypy_rc,
            "pytest_rc": pytest_rc,
            "coverage_rc": cov_rc,
            "bandit_rc": bandit_rc,
            "pip_audit_rc": pa_rc,
        },
        "logging_usage_detected": logging_usage(py_files),
    }
    return {
        "scores": scores,
        "total": total,
        "total_max": total_max,
        "weights": weights,
        "details": details,
        "suggestions": suggestions,
    }


def load_config(repo: Path) -> dict[str, Any]:
    p = repo / ".repoaudit.yml"
    if not p.exists() or yaml is None:
        return {}
    try:
        data = yaml.safe_load(read_text(p)) or {}
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


def print_summary(report: dict[str, Any]):
    scores = report["scores"]
    weights = report["weights"]
    total = report["total"]
    total_max = report["total_max"]
    d = report["details"]
    print("\n== Repo Readiness Audit ==")
    for k in [
        "Documentation",
        "Structure & Community",
        "Code Quality",
        "Testing",
        "Security",
        "CI/CD & Automation",
        "Reproducibility",
    ]:
        v = scores[k]
        mx = weights[k]
        bar = "#" * int((v / mx) * 20) if mx else ""
        print(f"{k:25s}: {v:5.1f} / {mx:2.0f}  [{bar:<20}]")
    print("-" * 55)
    print(f"{'TOTAL SCORE':25s}: {total:5.1f} / {int(total_max)}")
    print("\n--- Key Details ---")
    print(f"Project Version: {d['version']}")
    print(
        f"Python Files: {d['py_files']:<4} | Lines of Code: {d['py_lines']:<5} | "
        f"Docstring Coverage: {d['docstring_coverage']:.1%}"
    )
    print(f"Tests Detected: {d['tests_detected']}")
    print("\n[CI/CD & Automation]")
    ci = d["ci_details"]
    if ci["workflows"]:
        print(f"  Workflows: {', '.join(ci['workflows'])}")
        print(f"  Build Matrix Detected: {ci['has_matrix']}")
        print(f"  Tested OS: {', '.join(ci['tested_os']) or 'None'}")
        print(f"  Tested Python Versions: {', '.join(ci['tested_py']) or 'None'}")
        if ci["missing_permissions"]:
            print(f"  Missing permissions in jobs: {', '.join(ci['missing_permissions'])}")
        if ci["unversioned_actions"]:
            print(f"  Unpinned actions: {', '.join(ci['unversioned_actions'])}")
    else:
        print("  No CI workflows found in .github/workflows/")
    print("\n[Reproducibility & Dependencies]")
    pp = d["pyproject"]
    req = d["requirements"]
    if pp.get("version") or pp.get("python_requires") is not None or pp.get("dependencies"):
        print(
            "  pyproject.toml: Found | Python Requires: "
            f"{pp.get('python_requires') or 'Not specified'}"
        )
        print(f"  Dependencies in pyproject: {len(pp.get('dependencies', []))}")
    else:
        print("  pyproject.toml: MISSING")
    if req["exists"]:
        print(f"  requirements.txt: Found | Pinned: {req['pinned']}/{req['total']}")
    print("\n[Security]")
    print(f"  Secret Hits (sample): {d['secret_hits_sample'] or 'None'}")
    if d["static_security_findings"]:
        print(f"  Static Security Findings (sample): {d['static_security_findings']}")
    if report["suggestions"]:
        print("\n[Top Suggestions]")
        for s in report["suggestions"][:8]:
            print(f"  - {s}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Offline-first repo audit for public release readiness"
    )
    ap.add_argument("--path", default=".", help="Path to repository root")
    ap.add_argument("--json", help="Write JSON report to this path")
    ap.add_argument(
        "--strict", action="store_true", help="Exit nonzero if below --min-score or critical issues"
    )
    ap.add_argument(
        "--min-score", type=float, default=0.0, help="Minimum score required when --strict is set"
    )
    ap.add_argument(
        "--no-static-security",
        action="store_true",
        help="Skip static AST/text security linting heuristics",
    )
    args = ap.parse_args()
    print("Running repo audit, this may take a while...")
    root = Path(args.path).resolve()
    if not root.exists():
        print(f"ERROR: path not found: {root}", file=sys.stderr)
        return 2
    config = load_config(root)
    report = score_repo(root, config, disable_static_security=args.no_static_security)
    print_summary(report)
    if args.json:
        try:
            def ser(o):
                if isinstance(o, set):
                    return sorted(o)
                if isinstance(o, Path):
                    return str(o)
                return o
            Path(args.json).write_text(json.dumps(report, indent=2, default=ser), encoding="utf-8")
            print(f"\nWrote detailed JSON report to {args.json}")
        except Exception as e:  # pragma: no cover
            print(f"\nERROR: failed to write JSON: {e}", file=sys.stderr)
            return 3
    if args.strict:
        crit = False
        d = report["details"]
        if d["secret_hits_sample"] or d["static_security_findings"]:
            crit = True
        if report["total"] < max(args.min_score, 0):
            return 4
        if crit:
            return 5
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    sys.exit(main())
