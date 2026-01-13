# Code Smell: Missing Explicit Return Statement

**Labels:** `code-quality`, `refactoring`, `low-priority`  
**Type:** Code Clarity

## Description

The `get_parser_for_email` method in `ParserHelper` doesn't have an explicit `return None` statement at the end, relying on Python's implicit None return.

## Location

- `core/parsers/parser_helper.py` (line 51, end of method)

## Current Code

```python
@staticmethod
def get_parser_for_email(
    from_header: str,
) -> HeyBancoParser | NubankParser | RappiParser | BanorteParser | None:
    """Determine the appropriate parser instance..."""
    from_lower = from_header.lower()
    for bank, emails in bank_emails.items():
        if any(email.lower() in from_lower for email in emails):
            return PARSERS.get(bank)
    # Missing explicit return None
```

## Impact

- **Code Clarity:** Implicit behavior is less obvious
- **Maintainability:** May confuse developers unfamiliar with Python's implicit None return
- **Best Practice:** PEP 8 recommends explicit returns when a function can return None
- **Intent:** Doesn't clearly communicate "no parser found" case

## Proposed Solution

Add explicit return statement at the end:

```python
@staticmethod
def get_parser_for_email(from_header: str) -> BaseBankParser | None:
    """
    Determine the appropriate parser instance based on the email's From header.

    Args:
        from_header: The raw From: header value from the email

    Returns:
        An instantiated parser for the matching bank, or None if no match is found
    """
    from_lower = from_header.lower()
    for bank, emails in bank_emails.items():
        if any(email.lower() in from_lower for email in emails):
            return PARSERS.get(bank)
    
    return None  # ← Explicit: No matching parser found
```

## Acceptance Criteria

- [ ] Add explicit `return None` statement
- [ ] Verify all tests still pass
- [ ] Consider adding a log message for debugging:
  ```python
  logger.debug("No parser found for email from: %s", from_header)
  return None
  ```

## Priority

**Low** - This is a minor code clarity issue. While it's good practice to be explicit, the current code works correctly.

## Related Issues

- #5 (Feature Envy in Parser Return Type) - Should be fixed together
