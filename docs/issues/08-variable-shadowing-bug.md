# Bug: Variable Shadowing (Duplicate Assignment)

**Labels:** `bug`, `high-priority`, `easy-fix`  
**Type:** Code Error

## Description

Line 78 in `hey_banco.py` contains a duplicate assignment: `amount = amount = float(...)`. This is clearly a typo that should be fixed.

## Location

- `core/parsers/hey_banco.py` (line 78)

## Current Code

```python
amount_match = re.search(
    r"Cantidad\s*<br\s*/?>\s*<span\b[^>]*>([0-9]+(?:\.[0-9]+)?)</span>", text
)

if amount_match:
    amount = amount = float(amount_match.group(1).replace(",", ""))
    #       ^^^^^^^^ Duplicate assignment
```

## Impact

- **Code Quality:** Indicates careless coding or copy-paste error
- **Functional Impact:** While it still works, it's misleading
- **Code Review:** May confuse reviewers and future maintainers
- **Professional:** Makes the codebase look less polished

## Proposed Solution

Remove the duplicate assignment:

```python
if amount_match:
    amount = float(amount_match.group(1).replace(",", ""))
```

## Acceptance Criteria

- [ ] Remove duplicate assignment on line 78
- [ ] Verify the parser still works correctly
- [ ] Run any existing tests for HeyBancoParser
- [ ] Check for similar issues in other files (there's another similar case on line 117)

## Additional Findings

While investigating, found a similar duplicate assignment:
- Line 117: `amount = amount = float(amount_match.group(1).replace(",", ""))`

Both should be fixed in the same PR.

## Priority

**High** - This is an obvious bug that should be fixed quickly. While it doesn't break functionality, it indicates code quality issues and is very easy to fix.
