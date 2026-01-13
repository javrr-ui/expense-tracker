# Code Smell: Trailing Whitespace

## Type
Code Style

## Severity
Trivial

## Description
Found trailing whitespace in `base_parser.py` that should be removed to maintain code quality standards.

## Location
- `core/parsers/base_parser.py:24`
- `core/parsers/base_parser.py:57`

## Impact
- Pylint warning C0303 (trailing-whitespace)
- Inconsistent code style
- May cause unnecessary git diffs
- Most editors auto-remove trailing whitespace, leading to unintended changes

## Proposed Solution
Remove trailing whitespace from the affected lines.

## Effort Estimate
Trivial (1 minute)

## Related Files
- `core/parsers/base_parser.py`

## Additional Notes
Consider setting up:
1. Pre-commit hooks to automatically remove trailing whitespace
2. Editor configuration (.editorconfig) to prevent trailing whitespace
3. CI checks to fail on trailing whitespace
