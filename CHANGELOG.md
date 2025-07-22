# CHANGELOG

All changes implemented will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

- Non-existent `comparison_chart_TIMESTAMP.txt` file reference from output documentation (feature was implemented but not activated)

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

[Unreleased]: https://github.com/sMiNT0S/RealityCheckBench/releases/tag/v0.2.0-alpha...HEAD
[0.2.0-alpha]: https://github.com/sMiNT0S/RealityCheckBench/releases/tag/v0.2.0-alpha
[0.1.0-alpha]: https://github.com/sMiNT0S/RealityCheckBench/releases/tag/v0.1.0-alpha
