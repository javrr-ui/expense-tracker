# Code Smell: Duplicate SPANISH_TO_ENGLISH_MONTH Dictionary

## Type
Code Duplication (DRY Violation)

## Severity
Medium

## Description
The `SPANISH_TO_ENGLISH_MONTH` dictionary that maps Spanish month abbreviations to English is duplicated across multiple parser files. This violates the DRY (Don't Repeat Yourself) principle and makes maintenance difficult.

## Location
The same dictionary appears in:
- `core/parsers/rappi.py` (lines 22-35)
- `core/parsers/nubank.py` (lines 23-36)
- `core/parsers/banorte.py` (lines 36-49)

Additionally, `core/parsers/hey_banco.py` contains a similar but longer mapping (lines 143-156) with full month names instead of abbreviations.

## Current Code
```python
SPANISH_TO_ENGLISH_MONTH = {
    "ene": "Jan",
    "feb": "Feb",
    "mar": "Mar",
    "abr": "Apr",
    "may": "May",
    "jun": "Jun",
    "jul": "Jul",
    "ago": "Aug",
    "sep": "Sep",
    "oct": "Oct",
    "nov": "Nov",
    "dic": "Dec",
}
```

## Impact
- Code duplication increases maintenance burden
- Changes to the mapping need to be made in multiple places
- Risk of inconsistencies if updates are not synchronized
- Detected by pylint as R0801 (duplicate-code)

## Proposed Solution
1. Create a new module `core/parsers/date_utils.py` to centralize date-related utilities
2. Move both the abbreviated and full month name mappings to this module
3. Create helper functions for common date parsing operations
4. Update all parsers to import from the centralized module

## Example Solution
```python
# core/parsers/date_utils.py
SPANISH_MONTH_ABBR_TO_ENGLISH = {
    "ene": "Jan",
    "feb": "Feb",
    # ... rest of mappings
}

SPANISH_MONTH_FULL_TO_ENGLISH = {
    "enero": "January",
    "febrero": "February",
    # ... rest of mappings
}

def normalize_spanish_month(date_str: str, use_full_names: bool = False) -> str:
    """Normalize Spanish month names to English for parsing."""
    # Implementation
```

## Effort Estimate
Small (1-2 hours)

## Related Files
- `core/parsers/rappi.py`
- `core/parsers/nubank.py`
- `core/parsers/banorte.py`
- `core/parsers/hey_banco.py`
