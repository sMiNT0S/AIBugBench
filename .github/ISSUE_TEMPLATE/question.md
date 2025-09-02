---
name: Question or Support Request
about: Ask questions about setup, usage, or interpreting results
title: '[QUESTION] '
labels: ['question']
assignees: ''

---

## Question Type
<!-- Check the most appropriate category -->
- [ ] Setup and Installation
- [ ] Usage and Running Benchmarks
- [ ] Understanding Results
- [ ] Adding AI Models
- [ ] Cross-Platform Issues
- [ ] Other

## Your Question
<!-- Please describe your question clearly -->

## Environment Information

**Operating System:** <!-- Windows 10/11, macOS version, Linux distribution -->
**Python Version:** <!-- python --version -->
**AIBugBench Version:** <!-- Latest commit hash or version -->

## What You've Tried
<!-- If applicable, list what you've already attempted -->

## Context/Background
<!-- Any additional context that might help answer your question -->

## Expected Outcome
<!-- What result or information are you looking for? -->

---

### Before Submitting

- [ ] I've checked the [README FAQ section](../../README.md#frequently-asked-questions)
- [ ] I've reviewed the [Getting Started guide](../../docs/getting-started.md)
- [ ] I've searched existing issues for similar questions
- [ ] I've provided clear environment information above

### Common Quick Answers

- **Setup Issues**: See [Getting Started](../../docs/getting-started.md) for step-by-step setup
- **Results Location**: Check `/results` directory for timestamped files
- **Python Version**: Requires Python 3.13+ with modern syntax features
- **Cross-Platform**: Windows commands use `xcopy`, Unix/macOS use `cp -r`
- **Prompt 4 Testing**: Uses `unittest.mock` for behavioral testing, not real network calls
