# Code Smell: Duplicate Month Mapping Dictionaries

**Labels:** `code-quality`, `refactoring`, `medium-priority`  
**Type:** Code Duplication

## Description

The Spanish-to-English month mapping dictionary is duplicated across multiple parser files, violating the DRY (Don't Repeat Yourself) principle. This creates maintenance burden and risk of inconsistency.

## Locations

The same or similar month mapping appears in:
- `core/parsers/hey_banco.py` (lines 143-156)
- `core/parsers/rappi.py` (lines 22-35)
- `core/parsers/banorte.py` (lines 36-49)
- `core/parsers/nubank.py` (lines 23-36)

## Current Code

Each parser has variations of:
```python
SPANISH_TO_ENGLISH_MONTH = {
    "ene": "Jan",
    "feb": "Feb",
    "mar": "Mar",
    # ... etc
}
```

## Impact

- **Maintenance Burden:** Changes must be replicated in 4 locations
- **Risk of Inconsistency:** If one mapping is updated and others aren't
- **Code Bloat:** Unnecessary duplication across files
- **Testing Overhead:** Same logic needs to be tested multiple times

## Proposed Solution

1. Create a shared date utilities module:
   ```python
   # core/parsers/date_utils.py
   SPANISH_TO_ENGLISH_MONTH = {
       "ene": "Jan",
       "enero": "January",
       "feb": "Feb",
       "febrero": "February",
       # ... complete mapping
   }
   
   def normalize_spanish_date(date_str: str) -> str:
       """Normalize Spanish date string to English format."""
       # Common date normalization logic
       pass
   ```

2. Update all parsers to import from the shared module:
   ```python
   from core.parsers.date_utils import SPANISH_TO_ENGLISH_MONTH
   ```

3. Consider extracting common date parsing logic into reusable functions

## Acceptance Criteria

- [ ] Create `core/parsers/date_utils.py` with comprehensive month mappings
- [ ] Update all 4 parser files to import the shared constant
- [ ] Remove duplicate definitions from parser files
- [ ] Verify all parsers still work correctly with existing test data
- [ ] Add unit tests for the shared date utilities

## Related Issues

- #2 (Duplicate Date Normalization Logic)
