#!/usr/bin/env bash
# Pre-commit hook template for AIBugBench durability
# Copy to .git/hooks/pre-commit and chmod +x .git/hooks/pre-commit
# Purpose:
#  - Block unexpected empty files (excluding placeholders)
#  - Run fast lint (ruff) and a smoke subset of tests for quick feedback
#  - Avoid full coverage (done in CI / explicit script)

set -euo pipefail

ALLOW_EMPTY_REGEX='(^|/)(LICENSE|README.md|CONTRIBUTING.md|CODE_OF_CONDUCT.md|SECURITY.md|\.gitkeep)$'

# 1. Detect newly added / modified empty files
empty_files=$(git diff --cached --name-only --diff-filter=ACM | while read -r f; do
  [ -f "$f" ] || continue
  if [ ! -s "$f" ]; then
    echo "$f"
  fi
done)

violations=""
while read -r ef; do
  [ -z "$ef" ] && continue
  if [[ ! "$ef" =~ $ALLOW_EMPTY_REGEX ]]; then
    violations+="$ef\n"
  fi
done <<< "$empty_files"

if [ -n "$violations" ]; then
  echo 'ERROR: Empty non-placeholder files detected:' >&2
  echo -e "$violations" >&2
  echo 'Fix or remove them (or update ALLOW_EMPTY_REGEX) before committing.' >&2
  exit 1
fi

# 2. Fast lint (only changed Python files)
py_changed=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.py$' || true)
if [ -n "$py_changed" ]; then
  echo 'Running ruff on changed Python files...'
  ruff check $py_changed || exit 1
fi

# 3. Smoke tests (markers or selected fast files)
# Adjust pattern if you add @pytest.mark.smoke
if command -v pytest >/dev/null 2>&1; then
  echo 'Running smoke tests (subset)...'
  pytest -q -k 'list_files or secret_scan' || exit 1
fi

exit 0
