# Code Smell: Feature Envy in Parser Return Type

**Labels:** `code-quality`, `refactoring`, `low-priority`, `design`  
**Type:** Design Smell

## Description

The `get_parser_for_email` method in `ParserHelper` returns a union of specific parser types instead of the base `BaseBankParser` type, creating tight coupling and violating the Open/Closed Principle.

## Location

- `core/parsers/parser_helper.py` (lines 33-51)

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
```

## Impact

- **Tight Coupling:** Return type explicitly lists all concrete parser types
- **Maintenance Burden:** Every new parser requires updating this return type annotation
- **Open/Closed Violation:** Class must be modified when extended
- **Unnecessary Detail:** Callers don't need to know about specific implementations

## Proposed Solution

Change return type to base class:

```python
@staticmethod
def get_parser_for_email(from_header: str) -> BaseBankParser | None:
    """
    Determine the appropriate parser instance based on the email's From header.

    The matching is case-insensitive and checks if any of the known sender
    email addresses for a bank appear in the From header.

    Args:
        from_header: The raw From: header value from the email

    Returns:
        An instantiated parser for the matching bank, or None if no match is found
    """
    from_lower = from_header.lower()
    for bank, emails in bank_emails.items():
        if any(email.lower() in from_lower for email in emails):
            return PARSERS.get(bank)
    
    return None  # Explicit return (fixes #6)
```

## Benefits

- **Loose Coupling:** Callers work with base interface
- **Open/Closed Compliance:** Can add new parsers without changing this method
- **Type Safety:** Still maintains type checking through base class
- **Simplicity:** Cleaner, simpler type annotation

## Acceptance Criteria

- [ ] Change return type to `BaseBankParser | None`
- [ ] Add explicit `return None` statement
- [ ] Verify type checking still works
- [ ] Update any code that depends on specific parser types (unlikely)
- [ ] Run all tests to ensure no regressions

## Related Issues

- #6 (Missing explicit return statement)
