# Code Smell: Duplicate Date Normalization Logic

**Labels:** `code-quality`, `refactoring`, `medium-priority`  
**Type:** Code Duplication

## Description

The date normalization logic (Spanish months to English, AM/PM conversion) is duplicated within the `HeyBancoParser` class. The same ~27 lines of code appear in two different methods.

## Locations

- `core/parsers/hey_banco.py` - `_parse_outgoing_transfer()` (lines 143-169)
- `core/parsers/hey_banco.py` - `_parse_credit_card_payment()` (lines 226-253)

## Current Code

Both methods contain identical normalization logic:
```python
# Normalize Spanish months and AM/PM to English equivalents
month_map = {
    "enero": "January",
    "febrero": "February",
    # ... etc
}

normalized_date_str = date_str
for spanish, english in month_map.items():
    normalized_date_str = normalized_date_str.replace(spanish, english)
    normalized_date_str = normalized_date_str.replace(
        spanish.capitalize(), english
    )

# Normalize "a. m." and "p. m." to "AM" / "PM"
normalized_date_str = normalized_date_str.replace("a. m.", "AM").replace(
    "p. m.", "PM"
)

try:
    datetime_obj = date_parser(normalized_date_str, dayfirst=True)
except (ValueError, TypeError, OverflowError) as e:
    logger.error(...)
```

## Impact

- **Code Duplication:** ~27 lines duplicated exactly
- **Bug Risk:** Bug fixes need to be applied in multiple places
- **Readability:** Makes methods longer and harder to understand
- **Maintenance:** Changes to date parsing logic require updates in 2 places

## Proposed Solution

Extract the normalization logic into a private helper method:

```python
def _normalize_spanish_date(self, date_str: str) -> str:
    """
    Normalize Spanish date string to English format.
    
    Converts:
    - Spanish month names to English
    - "a. m." / "p. m." to "AM" / "PM"
    
    Args:
        date_str: Raw date string in Spanish format
        
    Returns:
        Normalized date string ready for parsing
    """
    month_map = {
        "enero": "January",
        "febrero": "February",
        "marzo": "March",
        "abril": "April",
        "mayo": "May",
        "junio": "June",
        "julio": "July",
        "agosto": "August",
        "septiembre": "September",
        "octubre": "October",
        "noviembre": "November",
        "diciembre": "December",
    }
    
    normalized = date_str
    for spanish, english in month_map.items():
        normalized = normalized.replace(spanish, english)
        normalized = normalized.replace(spanish.capitalize(), english)
    
    normalized = normalized.replace("a. m.", "AM").replace("p. m.", "PM")
    return normalized

def _parse_date(self, date_str: str) -> datetime | None:
    """Parse normalized date string with error handling."""
    try:
        normalized = self._normalize_spanish_date(date_str)
        return date_parser(normalized, dayfirst=True)
    except (ValueError, TypeError, OverflowError) as e:
        logger.error("Failed to parse date: %s -> %s", date_str, e)
        return None
```

Then update both methods to use:
```python
datetime_obj = self._parse_date(date_str.strip())
```

## Acceptance Criteria

- [ ] Create `_normalize_spanish_date()` helper method
- [ ] Create `_parse_date()` helper method with error handling
- [ ] Update `_parse_outgoing_transfer()` to use helper methods
- [ ] Update `_parse_credit_card_payment()` to use helper methods
- [ ] Verify both methods produce identical results with test data
- [ ] Reduce method lengths by ~20 lines each

## Related Issues

- #1 (Duplicate Month Mappings) - Should be resolved together
