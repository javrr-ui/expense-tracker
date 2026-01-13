# Bug: Redundant Code in RappiParser

## Type
Bug / Dead Code

## Severity
Trivial

## Description
In the `RappiParser.parse()` method, there is redundant code where `body_plain` is checked/assigned twice in succession.

## Location
`core/parsers/rappi.py:52-55`

## Current Code
```python
def parse(self, email_message, email_id: str) -> Transaction | None:
    subject = self._decode_subject(email_message.get("subject", ""))
    body = email_message.get("body_plain", "")

    if not body:
        body = email_message.get("body_plain", "")  # ← This is redundant
```

## Impact
- Dead code that serves no purpose
- Decreases code readability
- May cause confusion during code review

## Proposed Solution
The redundant check should either be removed or corrected to check for an alternative body format (like `body_html`):

**Option 1: Remove redundant code**
```python
def parse(self, email_message, email_id: str) -> Transaction | None:
    subject = self._decode_subject(email_message.get("subject", ""))
    body = email_message.get("body_plain", "")
```

**Option 2: Add fallback to HTML body (consistent with other parsers)**
```python
def parse(self, email_message, email_id: str) -> Transaction | None:
    subject = self._decode_subject(email_message.get("subject", ""))
    body = email_message.get("body_plain", "")

    if not body:
        body = email_message.get("body_html", "")  # ← Fallback to HTML
```

## Recommended Solution
Option 2 - Add fallback to HTML body for consistency with other parsers like `HeyBancoParser` and `BanorteParser`.

## Effort Estimate
Trivial (2 minutes)

## Related Files
- `core/parsers/rappi.py`
