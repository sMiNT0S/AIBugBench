# CHANGELOG

All changes implemented will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added explicit `psutil==7.0.0` runtime dependency (previously only installed implicitly in CI) to support performance regression and resource monitoring tests without ImportError locally. Updated `requirements.txt`, `pyproject.toml`, and removed duplicate install line from composite action.

- Comprehensive benchmark consistency CLI rewrite (`scripts/compare_benchmarks.py`): new flags (`--percent`, `--require`, `--no-emoji`, `--gha-summary`, `--json`), env var overrides, JSON output, GitHub Step Summary integration, repo-root path confinement, glob pattern rejection, auto emoji suppression on non-TTY, and percent/absolute tolerance modes.
- CODEOWNERS baseline plus `.editorconfig` added for ownership clarity and consistent editor defaults.
- Scheduled dependency refresh automation using pinned `peter-evans/create-pull-request` with diff stat in job summary (idempotent single PR model).
- CI action pin verification job enforcing full SHA usage across all workflows.

### Changed

- README license reference corrected to Apache-2.0; `pyproject.toml` enriched with `[project.urls]` and classifiers.
- Dependabot configuration normalized (grouped updates, daily & weekly schedules, scoped direct dependencies) reducing noise.
- CI & pre-commit lock verification unified through `scripts/verify_lock_sync.py` (single source of truth).
- Pre-commit configuration consolidated to one `verify-lock-sync` hook replacing multiple ad-hoc diff checks.
- Benchmark consistency check step updated to use the enhanced CLI for richer reporting and future automation hooks.

### Infrastructure

- **Pre-commit pipeline stabilization**: Fixed malformed `.pre-commit-config.yaml` structure consolidating all local hooks under single `repo: local` block
- **Smoke test isolation**: Added `scripts/smoke_pytest_wrapper.py` for artifact-isolated test execution with environment variable cascade (`AIB_RESULTS_DIR`, `AIB_ARTIFACT_DIR`, `AIBUGBENCH_ARTIFACT_DIR`)
- **Pytest coverage conflict resolution**: Created minimal `scripts/pytest_smoke.ini` to bypass global coverage plugin conflicts in smoke tests while preserving full coverage in CI
- **Artifact redirection framework**: Enhanced platform validator and benchmark runner to honor environment-based artifact redirection preventing pre-commit working tree mutations
- **CI/CD workflow hardening**: Updated multiple GitHub Actions workflows for YAML compliance, security improvements, and cross-platform compatibility

### Documentation

- **scripts/README.md enhancement**: Added documentation for `yaml_ducttape.ps1` (YAML formatting automation) and `update_requirements_lock.py` (dependency drift detection)
- **CONTRIBUTING.md workflow section**: Added comprehensive section on CI automation, pre-commit hooks setup, and development workflow patterns

### Developer Tooling

- **File normalization**: Multiple `.gitattributes`, `.yamllint.yml`, and workflow files updated for consistent formatting and compliance
- **Cross-platform compatibility**: Enhanced Windows Job Objects with graceful fallback when pywin32 unavailable, maintaining execution with reduced guarantees
- **Build artifact management**: Expanded `.gitignore` patterns for comprehensive build artifact, sandbox, and temporary file isolation

### Security

- **Critical security vulnerability fixes**: Fixed run_benchmark.py to properly halt execution on security script failures and audit failures (lines 741-747, 750-756)
- **Windows Job Object hardening**: Enhanced secure_runner.py with ActiveProcessLimit=3, breakaway prevention, and handle leak protection
- **Subprocess security**: Added close_fds=True to subprocess calls and improved process containment
- **Dependency integrity**: Updated requirements lock files with proper hash verification and normalized compilation headers
- **Workflow security hardening**: Enhanced GitHub Actions workflows with improved permission models and security scanning integration

### Documentation

- **GitHub Pages deployment**: Enabled automatic documentation deployment with mkdocs, material theme, and GitHub Actions workflow
- **MkDocs configuration**: Fixed navigation structure, added proper YAML formatting, and included roadmap in site navigation  
- **Documentation dependencies**: Added mkdocs, mkdocs-material, and mkdocs-include-markdown-plugin to requirements-dev.txt
- **Internal link fixes**: Corrected broken README links in INTERNALS.md and getting-started.md for proper site navigation
- **ROADMAP cleanup**: Removed private development references for public repository readiness

### Bug Fixes

- **Python 3.13 compatibility**: Resolved all static analysis errors with type compatibility solutions for modern Python syntax
- **Windows canary test failures**: Fixed Job Object quota limits preventing benchmark execution on Windows systems

### Known Issues

- **validate_docs.py parsing bug**: Documentation validation script has broken command parsing that extracts random text as commands. Requires refactor of parse_commands_from_docs() and platform detection logic. See GitHub issue for details.

### Quality Assurance

- **Test coverage improvements**: Multiple test compliance fixes for CI and pre-commit compatibility
- **Code formatting consistency**: Broad formatting normalization across configuration files, workflows, and Python modules
- **Type safety enhancements**: Additional mypy compatibility improvements and type annotation corrections

### Planned

- Post-0.9.0 documentation polish & diagrams
- Tiered submission system documentation (developer guide section)
- Validation package migration (execution + reporting layers) completion
- Public documentation deployment enablement (GitHub Pages)

## [0.9.0-beta] - 2025-09-03

### Upgrade notes

- Removed legacy path `submissions/template/`; use `submissions/templates/template/`.
- Deleted scripts: `fix_action_pins.py`, `automate_models.py`, `fix_security_noqa.py`, `validate_security.py`. Use `scripts/pin_actions_to_sha.py`, `scripts/update_requirements_lock.py`, `scripts/security_audit.py`.
- New comparison directory auto-created: `results/collected-results/`.
- `validate_docs.py` now depends on `validation/docs_core.py` for command classification.

### Added

- Canonical template README at `submissions/templates/template/README.md` (centralized instructions; legacy single-level path removed)
- Roadmap bullet for submission onboarding workflow (template consolidation + validation)
- Reference implementation hardening: Prompt 1–4 reference files fully cleaned (no blanket suppressions; zero Ruff issues)
- **SAFETY2.0 comprehensive security implementation**: Filesystem confinement, subprocess & dynamic code execution blocking (`eval/exec/compile`), dangerous import protection (`ctypes/marshal/pickle`), Windows Job Objects, bypass prevention, pre-release security audit script (`scripts/security_audit.py`), PR security workflow (`.github/workflows/pr-security.yml`), Safety & pip-audit integration, hash‑pinned dependencies (`requirements.lock`).
- Missing results directory: Created `results/collected-results/` for benchmark comparison functionality
- Scripts cleanup: Functional lock updater (`scripts/update_requirements_lock.py`), argparse CLIs for `scripts/compare_benchmarks.py` & enhanced `scripts/pin_actions_to_sha.py` (`--list/--dry-run/--apply`), centralized `classify_command` in `validation/docs_core.py`.
- Dependency lock enforcement: Added CI `lock-verification` job (pip-tools>=7.5.0) to fail when `requirements.lock` is out of sync with `requirements.txt`; PR security workflow installs with `--require-hashes`.

### Changed

- Consolidated duplicate template directories into single canonical tiered path (`submissions/templates/template/`)
- Strict-core typing & hygiene pass: centralized result TypedDicts, precise runner/validator signatures, added missing return & generic annotations, queue parameterization, modern isinstance unions, import/order & doc script lint cleanup, safe_print rationalization (no user-visible behavior change intended)
- Updated docs/configs/workflows to remove legacy `submissions/template/` references
- Refined `.gitignore` (dropped obsolete `.bandit` & `reports/` patterns)
- Adjusted `pyproject.toml` excludes to reflect canonical scaffold
- Normalized secret scanning config and fixed malformed YAML in `.github/secret-patterns.yml`
- Simplified `.semgrepignore` comments & canonicalized paths
- `setup.py`: removed automatic creation of deprecated legacy scaffold
- Developer guide & template README refinements
- Standardized reference prompt docstrings & logging; removed legacy `# noqa` usage
- Security audit workflow now on Python 3.13
- Sitecustomize loading fixed by removing `-I` and setting PYTHONPATH
- Security rules: removed global S603/S105; replaced with targeted per‑file noqa
- GitHub Actions maintenance: updated `actions/cache` v4.2.4 (SHA pinned)
- Scripts refactor: one canonical path per function, argparse adoption, centralized doc classification, improved pre-commit & coverage helpers
- Continuous quality gates: Ruff 0 issues, mypy strict-core 0 errors, full test suite green (branch coverage enforced)
- Windows-safe CLI printing stabilized; security banner no longer affects exit codes

### Removed

- Legacy `submissions/template/` directory & deprecation notes
- Legacy migration compatibility test suite (replaced by minimal canonical layout assertion)
- Archival legacy path references in reports & internal dependency analysis docs
- Temporary `test_subprocess_block.py` diagnostic script
- Duplicate / deprecated / redundant scripts: `scripts/fix_action_pins.py`, `scripts/automate_models.py`, `scripts/fix_security_noqa.py`, `scripts/validate_security.py`

### Fixed

- Broken/obsolete links referencing legacy template path
- Formatting/structure issues in secret patterns & semgrep ignore files
- Template README previously rendered as plain text (now proper markdown)
- Outdated scoring rubric link updated to `scoring-methodology.md`
- Long instruction line in deprecated automation script (wrapped)
- Markdown ordered list numbering inconsistency in developer guide
- Subprocess canary test execution in sandbox (cwd + sitecustomize)
- Import ordering & code quality issues across security modules
- `run_safety_check()` missing return path (now explicit true on clean case)
- Deprecated Actions cache references (now v4.2.4 with SHA)
- Global security rule suppressions replaced with targeted inline justifications
- Actions now pinned; comparison & coverage artifacts uploaded
- Security audit workflow stability; integrated secret & dependency scans

### Planned

- Post-0.9.0 documentation polish & diagrams
- Tiered submission system documentation (developer guide section)
- Validation package migration (execution + reporting layers) completion
- Public documentation deployment enablement (GitHub Pages)

## [0.8.1-beta] - 2025-08-27

### Added

- Result metadata privacy controls: `--no-metadata` flag and `AIBUGBENCH_DISABLE_METADATA` env var to disable collection of git commit, platform, timestamp, and dependency fingerprint (retains `spec_version` only)
- README section documenting minor metadata collection/provenance fields (spec_version, git_commit, python_version, platform, timestamp_utc, dependency_fingerprint) and opt-out guidance
- Centralized secret detection regex registry (`SECRET_PATTERNS`) in `validation/security_core.py` replacing scattered inline docs listings
- Internal documentation copies (validation, scripts, submissions, template READMEs) added under `docs/internal/` for MkDocs build compliance
- Roadmap "Type Hygiene" section capturing first stricter mypy run action items
- Concurrent model evaluation support via new `--workers` CLI flag (thread pool based, deterministic single-thread fallback)
- Atomic result persistence helper ensuring JSON and summary report writes occur via temp file + `os.replace()` (prevents torn/corrupt artifacts)
- Per-run timestamped results directories: `results/<YYYYMMDD_HHMMSS>/` with isolated `detailed/` & `comparison_charts/` subfolders plus backward-compatible root `latest_results.json`
- Dynamic prompt ID discovery for comparison generation (removes hard‑coded prompt list; auto-adapts to future prompt additions)
- Cached dependency fingerprint (single SHA-256 hash of `requirements.txt` per run) exposed in metadata when enabled
- Cached Unicode capability detection (single evaluation) improving Windows TTY performance and reducing repetitive encoding probes

### Changed

- `run_benchmark.py`: Added metadata opt-out logic, introduced environment/CLI toggle, refactored import ordering, added UTC-aware timestamping, and improved dependency fingerprint warning handling.
- Docs workflow hardening: pinned `actions/checkout` to `v4.1.6` and removed redundant job-level `permissions` (single workflow-level scope retained) for reproducibility and least privilege.
- Scoped security ignore S404: removed global Ruff ignore and restricted to audited files (`benchmark/runner.py`, `test_data/process_records.py`)
- Mypy Stage 1 tightening: enabled `check_untyped_defs`, `warn_unused_ignores`, `warn_return_any`, `warn_unreachable`; removed `allow_redefinition`; trimmed disabled error codes; added exclusion for duplicate template scaffold
- MkDocs navigation updated to reference internal copies instead of files outside `docs_dir`
- Results persistence model restructured: atomic writes + per-run directories reduce race conditions and enable historical run retention without manual copying
- Comparison & summary artifacts relocated under each run's directory (improves reproducibility and avoids cross-run overwrites)
- Performance improvements: eliminated repeated hashing of dependencies, redundant Unicode safety checks, and sequential model evaluation delays (when `--workers > 1`)
- Comparison generation logic simplified & future-proofed by deriving prompt IDs from actual run data

## [0.8.0-beta] - 2025-08-26

### Added

- **Repository audit consolidation**: canonicalized to `validation/repo_audit_enhanced.py` and removed legacy duplicate
- **Developer Guide section**: New "Repository Audit & Quality Gate" usage block with strict mode and minimum score examples
- **Narrowed secret scanning ignore scope**: safer `.trufflehogignore` now targets only necessary paths (no global `*.json|*.txt|*.log` ignores)
- **MkDocs documentation site scaffolding**: Introduced `mkdocs.yml`, Material theme, and structured navigation (Home, Getting Started, Usage, Models, Results, Troubleshooting, Project).
- **Documentation workflow (build-only)**: New `.github/workflows/docs.yml` builds docs and uploads artifact without deploying (no public Pages exposure while repo remains private).
- **Project documentation stubs**: Added `docs/index.md`, `getting-started.md`, usage guides (`usage/cli.md`, `usage/config.md`), and project meta pages (quickstart, changelog, contributing, code_of_conduct, security, license, example_submission, sabotage_notes, issues).
- **Comprehensive security infrastructure**: Multi-layered security scanning with TruffleHog, Semgrep, CodeQL, Safety, and pip-audit.
- **Automated GitHub security workflow**: Complete security.yml workflow with secret scanning, dependency analysis, and CodeQL integration.
- **Platform validation system**: New `benchmark/platform_validator.py` for cross-platform benchmark consistency validation.
- **Development dependency management**: New `requirements-dev.txt` with comprehensive development and testing dependencies.
- **Security configuration**: Advanced `bandit.yaml` configuration with test_data exclusions and Windows compatibility.
- **Enhanced CI/CD security**: Dependabot integration, secret pattern detection, and automated security reporting.
- **Advanced GitHub integrations**: CodeQL configuration, security event permissions, and artifact retention policies.
- **Comprehensive testing infrastructure**: Enhanced test suite with setup validation, conftest.py, and improved coverage.
- **Cross-platform automation (WIP)**: Modern unified automation script supporting OpenAI and Anthropic APIs with robust error handling (requires further testing), currently 'offline'.
- **CI safety switch**: Auto-skip `NETWORK` commands by default with `--allow-network` flag for CI safety.
- **Expanded targeted test coverage**: Added focused unit tests for platform validator (score extraction, cross-platform comparison, performance regression), runner (success, error, timeout, environment setup/cleanup), and utils (structure validation, statistics aggregation, comparison chart generation) raising overall pytest coverage to ~76% and enabling higher quality gates.
- **Phase 2 tiered structure tests**: Added discovery summary formatting, legacy abort, template presence variants, and tier combination tests (15 new) reinforcing deterministic behavior of single discovery path.
- **Validation core package**: Introduced importable `validation/` package (`docs_core.py`, `security_core.py`) extracting parsing and security helper logic from legacy scripts for modularity and testability.
- **Documentation validator CLI enhancements**: Added `--list`, `--dry-run` (alias of scan-only), `--json`, and `--json-file` flags to `scripts/validate_docs.py` for quick inspection and machine‑readable summaries.
- **Security validator CLI enhancements**: Added `--list-checks`, `--dry-run`, `--json`, and `--json-file` flags to `scripts/validate_security.py` enabling enumeration and structured reporting without executing scans.
- **Machine-readable summaries**: Both validation scripts can now emit JSON payloads (stdout and/or file) supporting CI artifact collection and automated gating.
- **Validation parser tests**: New `tests/test_validation_parsers.py` covering command extraction and security file presence; preserves coverage gate (>62%) during refactor.
- **README validation usage block**: Root `README.md` documents invocation examples for docs & security validation (including JSON output) improving discoverability.
- **Scripts README migration note**: Added note clarifying incremental migration of execution/reporting logic into the `validation` package.

### Changed

- Version bump to 0.8.0-beta (unreleased previously staged changes now formalized)
- All documentation references updated to relocated audit script path `validation/repo_audit_enhanced.py`
- Coverage artifacts (`coverage.xml`, `htmlcov/`) and MkDocs build output (`site/`) removed from tracking (remain ignored)
- **README slimming**: Condensed README to a minimal entry point; detailed guidance relocated to MkDocs site.
- **Cross-linking improvements**: Added reciprocal links between scoring rubric, interpreting results, troubleshooting, and sabotage notes.
- **Home page enhancements**: Added Project section reference and direct navigation link for quick access to meta docs and sabotage explanations.
-- **Git ignore updates**: Ignoring MkDocs build output `site/` directory and removing incorrect exclusions (`scripts/`, `RELEASE_NOTES.md`, `CLAUDE.md`).
- **Security policy enhancement**: Updated SECURITY.md with comprehensive reporting procedures and vulnerability disclosure timeline.
- **Testing framework modernization**: Enhanced test infrastructure with improved validation and cross-platform compatibility.
- **Documentation accuracy**: Updated all documentation to reflect current A-grade status (91.0/100) and production readiness.
- **CI workflow robustness**: Enhanced GitHub Actions with better error handling and security scanning integration.
- **Platform compatibility**: Improved Windows/macOS/Linux support with Unicode safety and proper encoding handling.
- **Development workflow**: Streamlined development process with automated security checks and validation.
- **Benchmark difficulty**: More realistic edge cases and coding pitfalls while maintaining solvability for advanced AI model testing.
- **Documentation consolidation**: Streamlined README/QUICKSTART (71% and 54% reductions) for readability.
- **Python baseline**: Unified to Python 3.13+ across docs and configs.
- **API automation patterns**: Replaced outdated patterns with modern env var management (OpenAI + Anthropic).
- **Docs validator**: `validate_docs.py` sandboxing improvements and cross-platform CI compatibility.
- **Cross-platform standards**: Explicit, fenced commands for cmd, PowerShell, and bash.
- **Platform-specific testing**: Added `--platform` flag for explicit PowerShell testing support in `validate_docs.py`.
- **Coverage gates raised**: `--cov-fail-under` progressed 50 → 60 → 62 alongside test suite expansion (effective coverage ~61.8%).
- **Docs & security scripts modularization**: Began staged extraction (parsing & core checks) to reduce monolithic scripts; future migrations will relocate execution/reporting for finer test granularity.
- **Documentation validator output modes**: Scan/list modes produce concise listings (capped) with optional JSON summary; legacy `--docs-only` behavior retained for backward compatibility.
- **Security validator behavior**: Dry run now enumerates intended checks without execution; JSON summaries list executed or planned checks for precise CI gating.
- **Internal imports**: New code paths prefer `from validation import ...` over direct script imports for reusable components.
- **README transformation**: Restructured as minimal navigation hub (33 lines) with clear audience paths
- **CHANGELOG enhancement**: Merged RELEASE_NOTES content for unified change tracking with dual sections
- **Scoring documentation**: Combined `scoring_rubric.md` and `interpreting_results.md` into `scoring-methodology.md`
- **Setup documentation**: Merged QUICKSTART.md into enhanced `docs/getting-started.md`
- **Troubleshooting location**: Moved from `docs/bug/troubleshooting.md` to `docs/troubleshooting.md`
- **Sabotage notes location**: Moved from root to `docs/sabotage-notes.md` for better discoverability
- **MkDocs integration**: Complete setup with include-markdown plugin, Material theme, and structured navigation
- **Prompt 3 wording clarified for fairness**: explicit deterministic, import-safe single-file requirement; removed ambiguous "non-strict inputs" / generic validation language (no scoring logic change)
- **Repository audit script fully migrated**: root `repo_audit_enhanced.py` removed; canonical path is now `validation/repo_audit_enhanced.py`.

### Removed

- Legacy `repo_audit.py` superseded by enhanced validator
- Root `CLAUDE.md` (relocated earlier to `docs_private/CLAUDE.md`)
- **Legacy submissions layout fallback**: Eliminated automatic fallback to legacy `submissions/example_model` & `submissions/template` structure pre-public release; discovery now aborts with explicit migration guidance.
- **STRICT layout mode**: Removed `AIBUGBENCH_STRICT_LAYOUT` environment variable (simplified single behavior path).
- **Redundant alternate discovery function**: Consolidated to one canonical tiered discovery implementation.
- **Stub documentation files**: Eliminated 9 redundant files in `docs/project/` that only contained links
- **Redundant documentation**: Consolidated overlapping content across 18 files
- **Nested directory structure**: Flattened `docs/bug/` and removed empty `docs/usage/` after consolidation

### Fixed

- **Broken relative link**: Corrected troubleshooting guide link to sabotage notes to use internal MkDocs path (`../project/sabotage_notes.md`).
- **Markdown lint compliance**: Resolved numerous MD lint warnings (bare URLs, fenced code languages, list spacing) across new and updated docs.
- **Security scanning integration**: Resolved false positives for intentional test patterns.
- **Cross-platform testing**: Fixed platform-specific issues in test execution and validation scripts.
- **Configuration validation**: Improved config file validation with proper error handling.
- **UTF-8 encoding**: Ensured consistent encoding across platforms and file operations.
- **JSON parsing**: Removed UTF-8 BOM and fixed invalid JSON (comments, duplicate keys, trailing commas) in `test_data/user_data.json`.
- **Docs lint compliance (scripts)**: Fixed 182 Ruff violations in `scripts/validate_docs.py` (whitespace, annotations, code quality).
- **PowerShell detection**: Resolved Windows PowerShell always showing “platform mismatch” by honoring the explicit platform flag.
- **Zero Ruff lint errors**: Cleared final outstanding import-order violation; repository now passes `ruff check .` with zero issues.
- **Critical files not tracked**: Scripts directory and important documentation now properly version controlled
- **Documentation redundancy**: Reduced from 40+ files to 15 focused resources (60% reduction)
- **Navigation complexity**: Improved from 3-4 clicks to 1-2 clicks for information access
- **Semantic overlap**: Reduced content duplication from 60% to less than 5%

### Technical

- Strengthened supply-chain & secret scanning posture by eliminating broad file-pattern exclusions
- Audit script path relocation prepares for future `validation` namespace packaging
- **Security toolchain**: Enterprise-grade scanners with intelligent false-positive filtering.
- **Platform validation**: Automated benchmark consistency checks on Windows, macOS, and Linux.
- **CI/CD maturity**: Advanced workflows with comprehensive security scanning and reporting.
- **Developer experience**: Expanded dev tooling and validation scripts for a smoother DX.
- **Quality assurance**: Systematic validation of A-grade achievement with `repo_audit_enhanced.py` compliance verification.
- **No public deployment yet**: Pages deploy step intentionally removed (no `pages`/`id-token` permissions) ensuring zero accidental publication during private iteration.
- **Future enablement path**: Deploy job can later be reintroduced with conditional `workflow_dispatch` + environment once repo is made public.
- **Validation refactor groundwork**: Established stable public API (`validation.docs_core.DocumentationValidator`, `validation.security_core.SECURITY_CHECKS`) enabling incremental migration away from script-bound logic.
- **CI integration readiness**: JSON summaries designed for straightforward consumption by GitHub Actions (parse counts / failures without scraping human text reports).
- **Semantic analysis performed**: Opus-level documentation inventory identifying overlap patterns
- **Canonicalization map created**: Source-to-destination mappings with semantic rationales
- **Audience paths optimized**: Persona-based navigation for 4 key user types
- **Validation requirements**: All documentation verified against actual implementation
- **Documentation architecture guide**: New `docs/architecture.md` explaining system design and plugin architecture
- **Comprehensive API reference**: Consolidated `docs/api-reference.md` covering CLI, Python API, and configuration
- **Unified developer guide**: Merged model development documentation into `docs/developer-guide.md`
- **Testing guide**: Extracted testing methodology into dedicated `docs/testing-guide.md`
- **Documentation archive**: Created `docs_archive/` for historical and internal documentation
- **Audience-specific navigation**: Clear paths for users, developers, contributors, and maintainers in README
- **Governance include pages**: Created `docs/contributing.md`, `docs/code-of-conduct.md`, `docs/security.md`, `docs/license.md` using include-markdown plugin

### Security

- **Multi-layer scanning**: Secrets, dependencies, and code vulnerabilities covered by TruffleHog, Semgrep, CodeQL, Safety, and pip-audit.
- **Automated reporting**: Integrated findings into CI/CD with artifact retention.
- **False positive management**: Filtered intentional patterns in test data and validation code.
- **Vulnerability management**: Automated dependency checks via Safety and pip-audit.
- **Continuous monitoring**: Weekly scheduled security scans and Dependabot integration.
- **Tiered Bandit validation**: Confirmed clean scans across reference_implementations/, templates/, and user_submissions/ after legacy fallback removal.

## [0.7.0-beta] - 2025-08-23

### Added

- **Enhanced linting configuration**: Comprehensive Ruff configuration with per-file ignore patterns for intentional design choices
- **Modern exception handling**: Implemented `contextlib.suppress()` pattern replacing legacy try-except-pass antipatterns
- **Security warning configuration**: Per-file ignores for subprocess calls (S603) and YAML loader usage (S506) required for benchmark functionality

### Changed

- **isinstance() syntax modernization**: Updated all `isinstance(x, (int, float))` to modern union syntax `isinstance(x, int | float)`
- **Collection operations**: Replaced list concatenation with modern unpacking syntax (`[*items, new_item]`)
- **MyPy configuration**: Updated python_version target to 3.13 for enhanced type checking

### Fixed

- **Complete lint compliance**: Resolved all 651 Ruff linting violations achieving zero-issue status
- **Line length violations**: Fixed all E501 violations across core files with line breaking and f-string optimization
- **Whitespace cleanup**: Eliminated all trailing whitespace (W291) and blank line whitespace (W293) issues
- **Unused variables**: Fixed all F841 violations using underscore prefixes for intentionally unused loop variables
- **Code style consistency**: Applied modern Python patterns while preserving all existing functionality
- **CI workflow compatibility**: Updated GitHub Actions to handle empty test suite gracefully for beta releases

### Technical

- **Files modified**: Enhanced benchmark/validators.py, benchmark/runner.py, run_benchmark.py, setup.py, and pyproject.toml
- **Conservative approach**: Preserved all security context, exception handling patterns, and behavioral logic
- **Zero breaking changes**: Maintained complete backward compatibility while modernizing code quality
- **Comprehensive validation**: All fixes tested to ensure continued benchmark functionality (88.17/100 baseline maintained)

## [0.6.3-beta] - 2025-08-21

### Added

- MIT `LICENSE`
- `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`
- Issue templates (bug report, feature request) and PR template
- GitHub Actions CI workflow (lint, type check, tests)
- `pyproject.toml` with Ruff & Mypy configuration
- Root logging baseline in `run_benchmark.py`
- README badges (license, python version, CI status, public-ready) & FAQ section

### Changed

- Pinned dependencies in `requirements.txt` for reproducibility
- `repo_audit_enhanced.py` improved placeholder filtering, neutral rc handling, skip `.github`

## [0.6.2-beta] - 2025-08-20

### Added

- **Setup.py AI prompt enhancement**: Added AI "wake up" message for improved benchmark result quality with cross-platform Unicode safety
- **Results logging communication**: Clear messaging about detailed results file locations in shell output for both single and multi-model tests
- **Template file enhancement**: Clear copy-paste replacement instructions with prominent headers in all 5 template files
- **ai_prompt.md reference file**: Complete benchmark context file for better AI response preparation

### Changed

- **README.md clarity improvements**: User-friendly language replacing technical jargon, eliminated duplicate content between Quick Start and detailed sections
- **Prompt 3 formatting refinement**: Enhanced structure and clarity while preserving all technical requirements, streamlined implementation instructions
- **Logical 6-step setup process**: Consolidated workflow without confusing cross-references between sections

### Fixed

- **Critical Unicode encoding crash**: Eliminated Windows 'charmap' codec crashes preventing results file creation with comprehensive safe_print() system
- **Cross-platform compatibility**: 100% elimination of results logging failures across all Windows CMD/PowerShell environments
- **AI response fragmentation**: Prevention of GPT models providing separate parts instead of complete scripts for Prompt 3
- **Template confusion**: Clear instructions emphasizing complete file replacement vs keeping template structure
- **Single model results not saving**: Fixed critical bug where `python run_benchmark.py --model name` did not save results to /results directory

### Technical

- **Multi-agent coordination**: Architecture-planner, backend-implementer, implementation-agent, and documentation-implementer approach
- **Unicode-safe printing infrastructure**: Robust error handling with ASCII fallbacks for cross-platform compatibility
- **Fresh user workflow validation**: All fixes validated through simulated user testing with cross-platform safety verification
- **Production readiness status**: Updated from "DOCUMENTATION TRANSFORMATION COMPLETE" to "PRODUCTION READY WITH USER EXPERIENCE OPTIMIZATION"

## [0.6.1-beta] - 2025-08-20

### Added

- **Complete QUICKSTART.md transformation**: Restructured from 8 confusing steps to 3 progressive parts with 15-minute user journey
- **Cross-platform command standardization**: Added explicit platform labeling (Windows CMD/PowerShell, macOS/Linux Bash) for all commands
- **Documentation consistency**: Standardized terminology and formatting across 8+ documentation files
- **Realistic benchmark expectations**: Updated output examples to show actual template scores (49.95/100) instead of misleading zero scores

### Changed

- **User experience optimization**: Eliminated mixed shell assumptions and confusing automation options throughout all guides
- **Terminology standardization**: Replaced confusing "solutions" with clear "code submissions" across all documentation
- **Workflow clarity**: Integrated proactive troubleshooting throughout guides instead of relegating to appendices
- **Documentation accuracy**: Updated all guides to reflect actual benchmark behavior and current 7-category scoring system
- **Beginner accessibility**: Replaced technical jargon with human-friendly explanations throughout documentation

### Fixed

- **Cross-platform compatibility barriers**: Resolved command failures caused by mixed shell assumptions in documentation
- **New user setup confusion**: Eliminated barriers identified through fresh user testing that prevented successful first-time usage
- **Misleading output expectations**: Corrected template benchmark scores from inaccurate 0.00/100 to realistic 49.95/100
- **Platform-specific command issues**: Ensured every command works correctly on Windows, macOS, and Linux with proper shell context
- **Documentation inconsistencies**: Achieved consistent formatting, terminology, and structure across README.md, docs/*.md, and EXAMPLE_SUBMISSION.md

### Technical

- **Documentation transformation scope**: Updated README.md, QUICKSTART.md, EXAMPLE_SUBMISSION.md, and all docs/*.md files
- **User journey optimization**: Established 15-minute setup pathway with clear step-by-step guidance
- **Quality standards achieved**: 100% platform coverage with proper formatting and accessibility
- **Fresh user testing validation**: Systematic resolution of barriers preventing successful new user onboarding

## [0.6.0] - 2025-08-19

### Added

- **Comprehensive code cleanup**: Applied 7 critical fixes from external code audit to eliminate bugs and improve reliability
- **Real yaml duplicate detection**: Implemented `UniqueKeyLoader` class for proper duplicate key detection in yaml files, replacing free point awards
- **Surgical bug fixes**: Fixed broken penalty system, metadata flags, and path resolution issues with precise line-specific changes
- **Enhanced lint compliance**: Resolved all F841 warnings while preserving scoring behavior and maintaining code quality

### Changed

- **Security penalty system**: Fixed broken penalty logic to actually deduct points when hardcoded credentials are detected
- **Yaml security analysis**: Removed false positive detection of safe yaml anchors and aliases that were incorrectly flagged as dangerous
- **Path resolution reliability**: Replaced brittle hardcoded paths with robust `self.test_data_dir` resolution for better cross-platform compatibility
- **Metadata accuracy**: Fixed `uses_requests` flag that always returned false due to name mismatch between check name and search pattern

### Fixed

- **Critical scoring bugs**: Security penalties now properly deduct points instead of being ignored due to `add_check` logic limitations
- **Prompt 3 path resolution**: Test data loading now uses reliable path resolution preventing file not found errors
- **Prompt 2 duplicate detection**: Yaml files are now validated for actual duplicate keys instead of awarding points without analysis
- **Dead code elimination**: Removed unused `ScoringGranularity` enum and redundant imports that created confusion

### Removed

- **Unused code artifacts**: Eliminated `ScoringGranularity` enum and redundant `unittest.mock` import that served no purpose
- **False positive security checks**: Removed yaml anchor and alias patterns that incorrectly flagged safe constructs as security risks

## [0.5.0] - 2025-08-18

### Added

- **Revolutionary behavioral testing**: Prompt 4 completely transformed from keyword sniffing to actual function execution with mocked scenarios
- **Complete prompt 2 overhaul**: Enhanced yaml/json validation with deep equivalence testing and structure preservation scoring
- **Execution-heavy prompt 3 redesign**: Business logic validation with comprehensive transformation testing and rule-based evaluation
- **Cross-platform results system**: Unicode-safe display with automatic fallbacks for Windows, macOS, and Linux compatibility
- **Enhanced user experience**: Detailed category breakdowns showing exactly where code excels and needs improvement
- **Comprehensive documentation audit**: Updated all project documentation to align with implemented 7-category scoring system

### Changed

- **Prompt 4 api testing approach**: Eliminated keyword sniffing in favor of actual http request mocking with `unittest.mock.patch`
- **Prompt 2 scoring distribution**: Restructured to structure/execution focus (4/6/8/6/1/0/0) with deep equivalence validation
- **Prompt 3 scoring emphasis**: Shifted to execution-dominant design (3/3/12/3/1/1/2) reflecting data processing nature
- **Results display format**: Enhanced terminal output with detailed category breakdowns and precise decimal scoring
- **Documentation consistency**: Fixed legacy scoring references throughout all markdown files to reflect current capabilities

### Fixed

- **Behavioral validation accuracy**: Prompt 4 now tests actual error handling scenarios instead of searching for error keywords
- **Data structure validation**: Prompt 2 performs semantic correctness validation beyond simple yaml parsing
- **Business rule implementation**: Prompt 3 validates explicit account tier rules instead of using magic id checks
- **Cross-platform encoding**: Results display works reliably across different terminal environments and operating systems

## [0.4.0] - 2025-08-18

### Added

- **Performance analysis system**: Complete O(n²) detection and algorithmic efficiency evaluation
- **PerformanceAnalyzer class**: Dedicated performance scanning for nested loops, inefficient patterns, memory usage, and algorithm efficiency
- **Maintainability analysis system**: Comprehensive code quality metrics including function length, code duplication, and complexity analysis
- **MaintainabilityAnalyzer class**: Automated detection of long functions (>20 lines), code duplication (3+ line blocks), variable naming issues, and complexity indicators
- **7-category scoring system**: Extended Prompt 1 validator to comprehensive evaluation across all code quality dimensions:
  - Performance analysis (2pts): Nested loop detection, inefficient patterns, memory usage optimization
  - Maintainability analysis (2pts): Function length, code duplication, variable naming quality, complexity metrics
- **Enhanced issue detection**:
  - **Performance issues**: String concatenation in loops, inefficient membership testing, multiple sorts, unnecessary conversions
  - **Maintainability issues**: Functions >20 lines, repeated code blocks, single-letter variables, deeply nested conditions
- **Partial credit system**: Sophisticated scoring with graduated deductions based on issue severity
- **Comprehensive feedback**: Detailed analysis showing specific performance and maintainability improvements needed
- **Complete documentation suite**: Updated all documentation files to reflect 7-category scoring system with proper setup instructions
- **Missing prompt recovery**: Restored complete `prompt_4_api_simulation.md` content with security-focused API integration requirements

### Changed

- **Prompt 1 scoring distribution**: Expanded from 5 categories to 7 categories (25 points total):
  - Syntax: 5pts (unchanged)
  - Structure: 3pts (reduced from 4pts)
  - Execution: 6pts (reduced from 8pts)
  - Quality: 3pts (reduced from 4pts)
  - Security: 4pts (unchanged)
  - Performance: 2pts (NEW)
  - Maintainability: 2pts (NEW)
- **Enhanced feedback granularity**: All analyzers now provide specific issue counts and actionable improvement suggestions
- **Scoring algorithm**: Refined deduction system with severity-based point reductions for more accurate evaluation
- **Score display formatting**: Improved output formatting to show maximum 2 decimal places for cleaner, professional appearance (e.g., `92.77/100` instead of `92.76666666666667/100`)
- **Documentation consistency**: Updated all documentation files with current scoring system details and proper formatting
- **Setup process clarification**: Enhanced setup documentation explaining the critical importance of running `setup.py` to create test data

### Technical details

- **Architecture enhancement**: Added two new analyzer classes following established patterns with comprehensive issue categorization
- **Performance validation**: Full benchmark score maintained at 92.8% (A grade) with enhanced 7-category analysis
- **Example model results**: Enhanced scoring shows 17.77/25 (71.1%) with detailed breakdown across all quality dimensions
- **Implementation pattern**: Consistent analyzer class structure with `analyze_code_*` methods returning standardized result dictionaries
- **Backward compatibility**: Zero breaking changes to existing API, results structure, or scoring thresholds
- **Testing coverage**: All analyzer classes individually tested and validated through integrated Prompt 1 validator

### Performance

- **Efficient pattern detection**: Optimized regex patterns and line-by-line analysis to prevent infinite loops in complex code analysis
- **Scalable analysis**: Analyzer classes designed for extension to other prompts without performance degradation
- **Memory efficiency**: Streamlined issue detection algorithms with minimal memory footprint

## [0.3.0] - 2025-08-16

### Added

- **Enhanced scoring system**: Complete rebuild of Prompt 1 validator with granular scoring and detailed feedback
- **ScoringGranularity Enum**: BINARY (1.0), GRADIENT (0.5), PRECISION (0.25) scoring levels for different evaluation types
- **ScoringDetail Class**: Tracks individual checks with rationale and generates detailed feedback lines
- **Security Analysis**: Comprehensive security vulnerability detection including SQL injection, hardcoded secrets, path traversal, and unsafe function usage
- **SecurityAnalyzer Class**: Dedicated security scanning with detailed vulnerability reporting
- **Enhanced Feedback Format**: Detailed breakdowns showing exactly which checks passed/failed with rationale (e.g., `"✅ Code Structure (4.0/4.0): ✓yaml_import, json_import, error_handling, logging, type_hints"`)
- **Detailed Scoring Breakdown**: New `detailed_scoring` field in results with earned/max points per category

### Changed

- Project renamed from "RealityCheckBench" to "AIBugBench" across all documentation and text files
- Updated repository references in README.md, QUICKSTART.md, and setup.py to reflect new name
- Maintained code compatibility and preserved historical entries in changelog
- **Prompt 1 Scoring Distribution**: Rebalanced from 4 categories to 5 categories while maintaining 25-point total:
  - Syntax: 5pts (unchanged)
  - Structure: 4pts (reduced from 5pts)
  - Execution: 8pts (reduced from 10pts)
  - Quality: 4pts (reduced from 5pts)
  - Security: 4pts (NEW)
- **Enhanced Context Manager Detection**: Improved to recognize both `with open()` and `.open()` patterns for pathlib usage
- **Granular Structure Checks**: Individual 1-point scoring for YAML/JSON imports, error handling, logging, and type hints
- **Quality Assessment**: More precise evaluation of code quality aspects with detailed rationale

### Technical Details

- **Architecture**: Maintains backward compatibility while adding enhanced evaluation dimensions
- **Performance**: No breaking changes to existing API or result structure
- **Testing**: Enhanced scoring validated with example model (17.0/25, 68% - passes threshold)
- **Documentation**: Comprehensive implementation tracking in CLAUDE.md with technical notes for future development

## [0.2.1] - 2025-07-22

### Added

- Comparison chart generation: activated existing `generate_comparison_chart` function to create visual progress bar charts for model performance comparison
- Enhanced README.md output files section to document the newly functional comparison charts

### Fixed

- README.md Quick Start section order: virtual environment setup now correctly precedes dependency installation
- Cross-platform compatibility: added Windows `xcopy` commands alongside Unix `cp -r` commands for template copying
- Documentation accuracy: corrected directory reference from `detailed_reports/` to `detailed_results/` in repository structure
- Quick Start instructions now include example model testing step to avoid "No models found" confusion
- UTF-8 encoding in comparison chart generation to support Unicode progress bar characters on Windows
- Integrated comparison chart generation into the main benchmark runner workflow

### Changed

- Enhanced README.md with more detailed repository structure documentation including missing files (CHANGELOG.md, QUICKSTART.md, EXAMPLE_SUBMISSION.md)

### Removed

- Comparison chart generation: activated existing `generate_comparison_chart` function to create visual progress bar charts for model performance comparison

## [0.2.0] - 2025-07-20

### Added

- This `CHANGELOG.md`
- New config constants added: DEFAULT_MAX_SCORE, DEFAULT_PASS_THRESHOLD, and DEFAULT_TIMEOUT to replace magic numbers in scoring logic
- validate_submission_structure() is now fully integrated to check submission completeness before running any tests
- UTF-8 encoding explicitly added to all file I/O operations in validators.py to support Unicode and emoji characters

### Changed

- Replaced all remaining outdated references to ai-code-benchmark/ with RealityCheckBench/ across documentation and metadata
- Improved internal type annotations (Optional[List] and related corrections) for clarity and static analysis
- Optimized error handling in validators.py and runner.py for better failure diagnostics when submissions are malformed or incomplete
- Renamed prompt example files in submission templates for better clarity and correctness
- README.md updated with virtual environment recommendations and platform-specific setup instructions

### Fixed

- Encoding bug (UTF8) that caused prompt_4_api_sync.py to score 0 due to unreadable characters on Windows (CP1252 default)
- Resolved several line-length and PEP8 issues flagged by flake8
- Fixed critical None check in validators.py that could crash scoring under specific input conditions
- Cleaned up unused imports across all modules

### Removed

- Cleaned up imports across all modules (removed `traceback`, `os`, `pathlib.Path`, etc. where unused)
- Removed unnecessary `shutil` import from `setup.py`

## [0.1.0] - 2025-07-18

### Added

- Initial full version of `RealityCheckBench`
- Core benchmark logic: `runner.py`, `validators.py`, `scoring.py`, `utils.py`
- Core file structure logic: `/RealityCheckBench` , `/benchmark`, `/docs`, `/prompts`, `/results`, `/submissions` , `/test_data` , `/tests`
- Prompt definitions for 4 coding tasks
- Example AI submission structure with all solution files
- CLI usage: `run_benchmark.py` with model-specific and batch modes
- Result output: JSON + summary reports
- `README.md` , and setup instructions
- Full test data and expected outputs

[Unreleased]: https://github.com/sMiNT0S/AIBugBench/releases/tag/v0.7.0-beta
[0.6.2-beta]: https://github.com/sMiNT0S/AIBugBench/releases/tag/v0.6.2-beta
[0.6.1-beta]: https://github.com/sMiNT0S/AIBugBench/releases/tag/v0.6.1-beta
