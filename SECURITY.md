# Security Policy

This document describes how we handle, prevent, and respond to security issues in AIBugBench.

## 1. Reporting Security Vulnerabilities

We take security seriously. If you discover a vulnerability, report it privately.

**Do NOT open a public GitHub issue for undisclosed vulnerabilities.**

Send reports to: **<175650907+sMiNT0S@users.noreply.github.com>**

Please include:

- Description & impact
- Reproduction steps / proof-of-concept
- Affected version / commit (SHA if possible)
- Suggested remediation (optional)

### Response Targets

- Acknowledge: within 48 hours
- Initial assessment: within 7 days
- Coordinated fix & advisory: timeline proportional to severity

We currently support only the latest released (or main branch if unreleased) version for security fixes.

### Severity (informal)

| Level | Example impact |
|-------|----------------|
| Critical | Arbitrary code execution outside expected sandbox |
| High | Unauthorized file access, silent result tampering |
| Medium | Denial of service (resource exhaustion) |
| Low | Information disclosure (non-sensitive metadata) |
| Informational | Hardening suggestion / best practice gap |

## 2. Threat Model & Scope

Although the benchmark is “mostly offline,” risk still exists:

- Executing untrusted model/submission code (file system, environment, potential network egress)
- Supply chain compromise (malicious dependency update)
- Tampering with scoring logic or fixtures to bias results
- Secret leakage from local dev environments
- Resource exhaustion (runaway loops, large memory use, huge temp files)
- Cross-platform inconsistencies masking regressions

Out of scope: protecting production infrastructure, multi-tenant isolation, GPU workload sandboxing.

## 3. Implemented Security Measures

Execution & Quality Gates:

- **SecureRunner sandbox**: Comprehensive execution isolation with temp directory containment, environment variable scrubbing, and resource limits (CPU, memory, file size)
- **Process execution blocking**: Complete subprocess isolation blocking all process spawning (subprocess.run/call/Popen, os.system, os.exec*/spawn*/fork* family)
- **Dynamic code execution protection**: Blocks eval(), exec(), compile() and dangerous imports (ctypes, marshal, pickle)
- **Filesystem confinement**: Path validation preventing access outside sandbox boundaries with guards on open(), os.remove(), shutil.* operations
- **Windows Job Objects**: Platform-specific CPU/memory limits via pywin32 for real resource control (vs no-op resource module)
- Zero Ruff lint errors policy (style + selected security rules)
- ≥60% test coverage with focused unit tests around validators and runners
- Platform validation to detect cross-run or cross-platform drift

Static & Dynamic Scanning:

- **PR Security Automation**: Automated security checks in pull requests (Ruff security rules, Bandit, pip-audit, security audit validation)
- Bandit (configured via `pyproject.toml`)
- CodeQL (GitHub code scanning)
- Ruff security rules (`S` select on demand)
- **Security Audit Script**: Comprehensive validation with dynamic canary testing for all security vectors
- (Planned / referenced) Semgrep ruleset (add once config lands)

Secrets & Dependency Hygiene:

- GitHub secret scanning (native)
- TruffleHog (extended secret pattern sweep) — referenced in CHANGELOG
- pip-audit dependency vulnerability scanning (Safety tool also available with Safety 3.6.1)
- **Hash-pinned requirements**: `requirements.lock` provides cryptographic integrity verification via `pip install --require-hashes`
- Production deployments should use: `pip install --require-hashes -r requirements.lock`
- `requirements.txt` remains human-readable; `requirements.lock` is auto-generated with hashes
- Dependabot updates (version & security alerts)

Supply Chain Controls:

- Pinned base dependencies in `requirements.txt`
- Separate `requirements-dev.txt` for tooling isolation
- Manual review of dependency updates in PRs

Operational Safeguards:

- Unicode-safe output and path normalization (prevents encoding-related truncation attacks)
- Explicit platform labeling for commands reduces misuse and script injection risk
- Timeout handling in runner to limit long-hanging submissions

## 4. Sandbox & Safe Execution Guidelines

**Current Implementation:**

The benchmark includes a comprehensive `SecureRunner` sandbox that:

- Creates isolated temporary directories for execution
- Blocks all subprocess and process spawning operations
- Prevents dynamic code execution (eval/exec/compile)
- Restricts filesystem access to sandbox boundaries
- Implements resource limits (CPU, memory, file size)
- Uses Windows Job Objects for real limits on Windows platforms

**Technical Implementation Details:**

The security guards are loaded via `sitecustomize.py` mechanism which executes automatically in child Python processes:

```python
# Import guard pattern (simplified)
_builtins_import = __import__

def _safe_import(name, *args, **kwargs):
    banned = {"ctypes", "pickle", "marshal"}
    if name in banned:
        raise ImportError(f"{name} is disabled in sandbox")
    return _builtins_import(name, *args, **kwargs)

import builtins
builtins.__import__ = _safe_import
```

```python
# Subprocess blocking pattern (simplified)
import subprocess, os
def _deny(*a, **k): raise RuntimeError("Subprocess disabled")
subprocess.run = subprocess.call = subprocess.Popen = _deny
os.system = _deny
```

```python
# Filesystem bounds enforcement (simplified)
from pathlib import Path
SANDBOX_ROOT = Path(os.environ["AIBB_TMP"]).resolve()

def _inside(p: Path) -> Path:
    p = Path(p).resolve()
    p.relative_to(SANDBOX_ROOT)  # raises if outside
    return p
```

**Pre-run Security Gate:**

The benchmark **requires** a security audit to pass before any code execution:

```bash
python scripts/security_audit.py || exit 1
```

This audit validates that all security guards are active and prevents accidental regressions. The CLI refuses to run if security checks fail.

**Technical Notes:**

- Python's `-I` isolated mode prevents sitecustomize loading, so we use PYTHONPATH injection instead to ensure guards always load
- Guards provide explicit error messages when blocked operations are attempted
- Honest CLI banners show which protections are actually enforced vs. claimed

**Additional Recommendations for Enhanced Security:**

- Use a dedicated Python virtual environment
- Optionally run inside a disposable container or VM (planned future enhancement)
- Disable outbound network (firewall / OS policy) unless explicitly required
- Strip environment variables containing secrets before run
- Run with least privileges (non-admin user)
- Impose filesystem boundaries (bind mount only needed dirs) when containerizing

## 4.1 LLM/AI-Specific Considerations

- Safety precautions should still be taken when running LLM/AI generated code; it still matters because “private” + “I trust myself” doesn’t remove these risk sources:

- Model output is untrusted code: an LLM can hallucinate unsafe patterns (infinite loops, wide file glob deletes, exfiltration attempts).
- Prompt injection / data bleed: If you paste prior logs/secrets into a prompt, generated code might surface or propagate them.
- Transitive drift: Future you (or a collaborator) may run old submissions; hardening now prevents bad habits later.
- Supply chain: A dependency update plus model‑generated code can interact in unsafe ways (e.g., deprecated APIs encouraging insecure fallbacks).
- Local environment leakage: Even in a private repo, env vars (API keys, tokens) are present and accessible to executed code.
- Persistence bugs: Generated code might overwrite benchmark fixtures or results, biasing later comparisons.

## 5. Integrity & Reproducibility

- Deterministic test fixtures; no hidden datasets
- Platform validator compares results across platforms for drift or performance regression
- Results saved to `results/latest_results.json` (recommend committing or hashing for long-running studies)
- Encourage verifying scoring code changes via diff review + tests before accepting benchmark deltas

## 6. Disclosure & Patch Process

1. Private report received & triaged
2. Reproduce + assign severity
3. Develop fix on a private branch if impact warrants embargo
4. Add/update tests preventing regression
5. Publish fix (CHANGELOG entry + optional advisory summary)
6. Credit reporter if consent granted

## 7. Dependency Management & Supply Chain

- Regular Dependabot PRs reviewed by maintainers (no blind auto-merge)
- pip-audit vulnerability scanning for comprehensive advisory coverage (Safety tool also available with Safety 3.6.1)
- Prefer minimal dependency surface; additions must justify functionality gain
- **Hash-pinned requirements**: `requirements.lock` provides cryptographic integrity verification via `pip install --require-hashes`
- Production deployments should use: `pip install --require-hashes -r requirements.lock`
- `requirements.txt` remains human-readable; `requirements.lock` is auto-generated with hashes
- **Update process**: Run `python scripts/update_requirements_lock.py` when changing dependencies to regenerate hash-pinned lock file

## 8. Privacy & Telemetry

- Project performs **no outbound telemetry** or analytics calls
- Any network interaction would come only from user submissions or explicit optional flags

## 9. False Positives & Test Data

- Dummy secrets intentionally appear in `test_data/` or templates; scanners tuned/filtered
- If a real secret is ever committed, rotate immediately and purge history if needed
- Specific known benign hits (documented for transparency):
  - `tests/test_validators_parametric.py`: contains a hardcoded fake key string (`sk-ABCDEF0123456789TOKENXYZ`) used to exercise secret detection logic. It is not a real credential.
  - `validation/security_core.py`: includes regex patterns (e.g. `AKIA[0-9A-Z]{16}`) for detecting AWS style keys; these pattern literals may appear in scans.
  - These occurrences are safe; no live secrets are present. Any additional scan hit outside this list should be investigated.

## 10. Manual Security Validation (Cross-Platform Examples)

### Bash / Linux / macOS

```bash
pip install bandit pip-audit safety ruff
ruff check . --select S
bandit -r . -f json
pip-audit
safety scan --file=requirements.lock
python scripts/security_audit.py
```

### PowerShell

```powershell
pip install bandit pip-audit safety ruff
ruff check . --select S
bandit -r . -f json
pip-audit
safety scan --file=requirements.lock
python scripts/security_audit.py
```

## 11. Best Practices for Users

- Never commit real API keys; use obvious placeholders
- Review AI-generated code before trusting results
- Sanitize / validate new validator logic (avoid `eval`, unbounded recursion)
- Keep dependencies updated (apply Dependabot PRs promptly)
- Isolate benchmark execution from production data

## 12. Known & Planned Improvements

**Future Enhancements (Optional):**

- **Container/jail runner**: Optional isolation mode with docker/podman support providing OS-level egress blocking and read-only filesystem
- **Enhanced network isolation**: Kernel-level network blocking beyond current Python-level guards for adversarial use cases
- **User-namespace jails**: bubblewrap/nsjail integration for stronger process isolation in multi-tenant scenarios
- Semgrep ruleset integration (status: planned)
- Hash-based integrity verification for result JSON files

**Recently Implemented:**

- ✅ Consolidated safe subprocess wrapper (complete blocking implemented)
- ✅ PR security automation with comprehensive security checks
- ✅ Hash-pinned dependencies with cryptographic integrity verification
- ✅ Windows Job Objects for real resource limits
- ✅ Dynamic code execution and dangerous import protection

## 13. Contact & Questions

General (non-sensitive) questions: open a normal GitHub issue.
Sensitive security concerns: use the private reporting address above.

---
This policy will evolve; see the CHANGELOG for substantive security process updates.
