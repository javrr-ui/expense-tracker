# Bug: Inconsistent Body Selection Logic

**Labels:** `bug`, `code-quality`, `medium-priority`  
**Type:** Code Inconsistency / Bug

## Description

Different parsers have inconsistent logic for choosing between `body_html` and `body_plain` from email messages. Most notably, the Rappi parser has a clear bug where it fetches `body_plain` twice instead of having a fallback to HTML.

## Locations and Patterns

### 1. HeyBancoParser (Correct Pattern)
```python
# core/parsers/hey_banco.py (lines 46-49)
body = email_message.get("body_html", "")

if not body:
    body = email_message.get("body_plain", "")
```
✅ Prefers HTML, falls back to plain

### 2. RappiParser (BUG - Fetches plain twice)
```python
# core/parsers/rappi.py (lines 52-55)
body = email_message.get("body_plain", "")

if not body:
    body = email_message.get("body_plain", "")  # ← BUG: Should be body_html
```
❌ Bug: Same key accessed twice, no actual fallback

### 3. NubankParser (Only uses plain)
```python
# core/parsers/nubank.py (lines 63-64)
body = email_message.get("body_plain", "")
date = email_message.get("date", "")
```
⚠️ Never tries HTML, even if plain is empty

### 4. BanorteParser (Correct Pattern)
```python
# core/parsers/banorte.py (lines 80-83)
body = email_message.get("body_html", "")

if not body:
    body = email_message.get("body_plain", "")
```
✅ Prefers HTML, falls back to plain

## Impact

- **Rappi Parser Bug:** Will fail to parse emails that only have HTML body
- **NuBank Limitation:** Cannot parse emails that only have HTML body
- **Inconsistency:** Different parsers have different expectations
- **Testing Difficulty:** Tests need to account for different behaviors
- **Maintenance:** No clear standard for body selection

## Proposed Solution

### Option 1: Fix Individual Bugs
Minimal change to fix the immediate bugs:

```python
# In rappi.py - Fix the duplicate key access
body = email_message.get("body_plain", "")

if not body:
    body = email_message.get("body_html", "")  # ← Fixed

# In nubank.py - Add fallback to HTML
body = email_message.get("body_plain", "")

if not body:
    body = email_message.get("body_html", "")  # ← Added fallback
```

### Option 2: Implement Consistent Strategy in Base Parser

```python
# core/parsers/base_parser.py
class BaseBankParser(ABC):
    """Abstract base class for bank-specific email parsers."""
    
    bank_name = "generic"
    
    # Add preference for body type
    prefer_html_body = True  # Can be overridden by subclasses
    
    def get_email_body(self, email_message: dict) -> str:
        """
        Get email body with consistent fallback logic.
        
        Args:
            email_message: Parsed email message dict
            
        Returns:
            Email body (HTML or plain text based on preference)
        """
        if self.prefer_html_body:
            body = email_message.get("body_html", "")
            if not body:
                body = email_message.get("body_plain", "")
        else:
            body = email_message.get("body_plain", "")
            if not body:
                body = email_message.get("body_html", "")
        
        return body
    
    @abstractmethod
    def parse(self, email_message, email_id: str) -> Transaction | None:
        """Parse an email message to extract a transaction."""
```

Then update parsers:

```python
# In each parser's parse method
body = self.get_email_body(email_message)

# Or override preference if needed
class NubankParser(BaseBankParser):
    prefer_html_body = False  # NuBank emails work better with plain text
```

### Option 3: Use EmailMessage Model Helper

If implementing #11 (EmailMessage model), add helper property:

```python
@dataclass
class EmailMessage:
    # ... fields ...
    
    def get_body(self, prefer_html: bool = True) -> str:
        """Get email body with specified preference."""
        if prefer_html:
            return self.body_html or self.body_plain
        return self.body_plain or self.body_html
```

## Recommended Approach

**Option 2** (Base parser method) provides:
- Immediate bug fixes
- Consistent behavior across parsers
- Flexibility for parser-specific preferences
- Easier testing and maintenance

## Acceptance Criteria

### Immediate Fixes (High Priority)
- [ ] Fix Rappi parser bug (line 55)
- [ ] Add HTML fallback to NuBank parser
- [ ] Test both parsers with HTML-only and plain-only emails

### Long-term Improvement (Medium Priority)
- [ ] Implement `get_email_body()` method in base parser
- [ ] Update all parsers to use base parser method
- [ ] Add tests for body selection logic
- [ ] Document body selection strategy

## Testing

Add tests to verify:
```python
def test_rappi_parser_with_html_only_email():
    """Rappi parser should handle HTML-only emails."""
    email = {
        "body_html": "<html>Test content</html>",
        "body_plain": "",
        # ...
    }
    # Should not fail

def test_nubank_parser_with_html_only_email():
    """NuBank parser should handle HTML-only emails."""
    email = {
        "body_html": "<html>Test content</html>",
        "body_plain": "",
        # ...
    }
    # Should not fail
```

## Priority

**High** for Rappi bug fix (clear logic error)  
**Medium** for overall consistency improvement

## Related Issues

- #11 (Data Clump) - EmailMessage model could help standardize this
- #13 (Inconsistent Error Handling) - Part of broader consistency problem
