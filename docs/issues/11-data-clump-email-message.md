# Code Smell: Data Clump (email_message Dictionary)

**Labels:** `code-quality`, `refactoring`, `medium-priority`, `design`  
**Type:** Data Clump

## Description

The `email_message` dictionary is passed around throughout the codebase with inconsistent key access patterns. Different parsers access different combinations of keys (`body_html`, `body_plain`, `subject`, `date`), and there's no clear data contract or validation.

## Locations

- `core/fetch_emails.py` - Creates the dict (lines 48-56)
- All parser files - Access various keys inconsistently
- No formal data structure definition

## Current Pattern

```python
# Created in fetch_emails.py
payload = {
    "id": msg_id,
    "subject": email_msg.get("Subject", ""),
    "from": email_msg.get("From", ""),
    "to": email_msg.get("To", ""),
    "date": email_msg.get("Date", ""),
    "body_plain": "",
    "body_html": "",
}

# Used inconsistently in parsers
subject = email_message.get("subject", "")  # Different parsers, different keys
body = email_message.get("body_html", "")
# Sometimes body_plain, sometimes body_html, sometimes both
```

## Impact

- **No Contract:** Unclear what keys are guaranteed to exist
- **KeyError Risk:** Prone to errors if dict structure changes
- **Inconsistency:** Different parsers have different access patterns
- **Testing Difficulty:** Must mock dictionaries with exact keys
- **Type Safety:** No type checking on dictionary keys
- **Documentation:** Structure not formally documented

## Proposed Solution

Create an `EmailMessage` dataclass or Pydantic model:

```python
# core/models/email_message.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EmailMessage:
    """Structured representation of a parsed email message."""
    
    id: str
    subject: str
    from_address: str
    date: str
    to: str = ""
    body_plain: str = ""
    body_html: str = ""
    
    @property
    def body(self) -> str:
        """Get email body, preferring HTML if available."""
        return self.body_html or self.body_plain
    
    @property
    def body_text(self) -> str:
        """Get email body, preferring plain text if available."""
        return self.body_plain or self.body_html
```

Or using Pydantic for validation:

```python
from pydantic import BaseModel, Field

class EmailMessage(BaseModel):
    """Structured representation of a parsed email message."""
    
    id: str = Field(..., description="Gmail message ID")
    subject: str = Field(default="", description="Email subject line")
    from_address: str = Field(..., alias="from", description="Sender email address")
    date: str = Field(default="", description="Email date header")
    to: str = Field(default="", description="Recipient email address")
    body_plain: str = Field(default="", description="Plain text email body")
    body_html: str = Field(default="", description="HTML email body")
    
    class Config:
        populate_by_name = True
        
    @property
    def body(self) -> str:
        """Get email body, preferring HTML if available."""
        return self.body_html or self.body_plain
```

## Implementation Steps

1. Create `EmailMessage` model
2. Update `parse_email()` to return `EmailMessage` instead of dict
3. Update all parsers to work with `EmailMessage` objects
4. Add helper properties for common access patterns
5. Update type hints throughout codebase

## Acceptance Criteria

- [ ] Create `EmailMessage` dataclass or Pydantic model
- [ ] Update `parse_email()` return type
- [ ] Update all parser signatures to accept `EmailMessage`
- [ ] Update parser implementations to use model attributes
- [ ] Add helper properties for body selection
- [ ] Update all type hints
- [ ] Add tests for the new model
- [ ] Verify all parsers still work correctly

## Benefits

- **Type Safety:** Compile-time checking of attribute access
- **Clear Contract:** Documented structure with types
- **Better IDE Support:** Autocomplete for attributes
- **Validation:** Can add validation rules with Pydantic
- **Consistency:** Single source of truth for structure
- **Refactoring:** Easier to change structure in one place

## Related Issues

- #14 (Inconsistent body selection logic) - Would be addressed by helper properties
