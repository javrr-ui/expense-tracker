# Bug: Double Assignment and Typo in Code

## Type
Bug

## Severity
Low (cosmetic bug, no functional impact)

## Description
Found two instances of minor bugs that should be fixed:

1. **Double assignment in `hey_banco.py`**: Line 78 has `amount = amount = float(...)` which is redundant
2. **Similar issue in `banorte.py`**: Line 117 has the same double assignment pattern

## Location
- `core/parsers/hey_banco.py:78`
- `core/parsers/banorte.py:117`

## Current Code
```python
# In hey_banco.py line 78
if amount_match:
    amount = amount = float(amount_match.group(1).replace(",", ""))

# In banorte.py line 117
if amount_match:
    amount = amount = float(amount_match.group(1).replace(",", ""))
```

## Impact
- Redundant code that decreases readability
- May cause confusion during code review
- No functional impact (Python handles this correctly)

## Proposed Solution
Remove the duplicate assignment:

```python
# Should be:
if amount_match:
    amount = float(amount_match.group(1).replace(",", ""))
```

## Effort Estimate
Trivial (5 minutes)

## Related Files
- `core/parsers/hey_banco.py`
- `core/parsers/banorte.py`
