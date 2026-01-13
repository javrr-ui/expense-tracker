# Code Smell: Inconsistent Return Statements in Parser Methods

## Type
Code Quality / Inconsistent Behavior

## Severity
Medium

## Description
Several parser `parse()` methods have inconsistent return statements - some code paths return explicit values while others have implicit `None` returns. This is flagged by pylint as R1710 and can lead to confusion and potential bugs.

## Location
- `core/parsers/hey_banco.py:43` - `parse()` method
- `core/parsers/nubank.py:52` - `parse()` method
- `core/parsers/rappi.py:50` - `parse()` method
- `core/parsers/parser_helper.py:33` - `get_parser_for_email()` method

## Current Code Example
```python
# In hey_banco.py
def parse(self, email_message, email_id: str) -> Transaction | None:
    subject = self._decode_subject(email_message.get("subject", ""))
    body = email_message.get("body_html", "")

    if not body:
        body = email_message.get("body_plain", "")

    if self.SPEI_RECEPTION in subject:
        tx = self._parse_spei_reception(body, email_id)
        return tx

    if self.SPEI_OUTGOING in subject:
        tx = self._parse_outgoing_transfer(body, email_id)
        return tx

    # ... more conditions ...
    
    # Missing explicit return None at the end
```

## Impact
- Pylint warning R1710 (inconsistent-return-statements)
- Implicit returns can be confusing for code readers
- Inconsistent code style across the codebase
- Potential for misunderstanding the function's behavior

## Proposed Solution
Add explicit `return None` statements at the end of all methods that should return `None` when no conditions are met.

## Example Solution
```python
def parse(self, email_message, email_id: str) -> Transaction | None:
    subject = self._decode_subject(email_message.get("subject", ""))
    body = email_message.get("body_html", "")

    if not body:
        body = email_message.get("body_plain", "")

    if self.SPEI_RECEPTION in subject:
        tx = self._parse_spei_reception(body, email_id)
        return tx

    if self.SPEI_OUTGOING in subject:
        tx = self._parse_outgoing_transfer(body, email_id)
        return tx

    # ... more conditions ...
    
    return None  # Explicitly handle unsupported email types
```

## Effort Estimate
Trivial (30 minutes)

## Related Files
- `core/parsers/hey_banco.py`
- `core/parsers/nubank.py`
- `core/parsers/rappi.py`
- `core/parsers/parser_helper.py`
