# CHANGELOG

All changes implemented will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.2-beta] - 2025-08-20

### Added

- **Setup.py AI prompt enhancement**: Added AI "wake up" message for improved benchmark result quality with cross-platform Unicode safety
- **Results logging communication**: Clear messaging about detailed results file locations in shell output for both single and multi-model tests
- **Template file enhancement**: Clear copy-paste replacement instructions with prominent headers in all 5 template files
- **ai_prompt.txt reference file**: Complete benchmark context file for better AI response preparation

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

[Unreleased]: 
[0.6.1-beta]: https://github.com/sMiNT0S/AIBugBench/releases/tag/v0.6.1-beta


## Deprecated, tags removed. Keeping for clarity;
[Unreleased]: https://github.com/sMiNT0S/RealityCheckBench/releases/tag/v0.2.0-alpha...HEAD
[0.2.0-alpha]: https://github.com/sMiNT0S/RealityCheckBench/releases/tag/v0.2.0-alpha
[0.1.0-alpha]: https://github.com/sMiNT0S/RealityCheckBench/releases/tag/v0.1.0-alpha
