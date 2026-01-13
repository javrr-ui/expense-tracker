# Code Smells Identified in Expense Tracker

This document lists code quality issues (code smells) identified in the codebase. Each item includes a description, location, severity, and suggested remediation.

---

## 1. Duplicate Code: Month Mapping Dictionaries

**Severity:** Medium  
**Category:** Code Duplication

### Description
The Spanish-to-English month mapping dictionary is duplicated across multiple parser files, violating the DRY (Don't Repeat Yourself) principle.

### Locations
- `core/parsers/hey_banco.py` (lines 143-156)
- `core/parsers/rappi.py` (lines 22-35)
- `core/parsers/banorte.py` (lines 36-49)
- `core/parsers/nubank.py` (lines 23-36)

### Impact
- Maintenance burden: Changes must be replicated in 4 locations
- Risk of inconsistency if one mapping is updated and others aren't
- Unnecessary code bloat

### Suggested Fix
Create a shared constants module for date utilities:
```python
# core/parsers/date_utils.py
SPANISH_TO_ENGLISH_MONTH = {
    "ene": "Jan",
    "enero": "January",
    # ... etc
}
```
Then import this constant in all parsers that need it.

---

## 2. Duplicate Code: Date Normalization Logic

**Severity:** Medium  
**Category:** Code Duplication

### Description
The date normalization logic (Spanish months to English, AM/PM conversion) is duplicated in two methods within `HeyBancoParser`.

### Locations
- `core/parsers/hey_banco.py` - `_parse_outgoing_transfer()` (lines 143-169)
- `core/parsers/hey_banco.py` - `_parse_credit_card_payment()` (lines 226-253)

### Impact
- Same code appears twice with identical logic
- Bug fixes need to be applied in multiple places
- Makes the methods longer and harder to read

### Suggested Fix
Extract the normalization logic into a private helper method:
```python
def _normalize_spanish_date(self, date_str: str) -> str:
    # Month mapping and normalization logic
    pass
```

---

## 3. Magic Number: maxResults=500

**Severity:** Low  
**Category:** Magic Numbers

### Description
Hardcoded value `maxResults=500` in the Gmail API call without explanation.

### Location
- `core/fetch_emails.py` (line 23)

### Impact
- Unclear why 500 was chosen
- Makes it harder to adjust if API limits change
- Not configurable without code modification

### Suggested Fix
Define as a named constant at module level:
```python
MAX_MESSAGES_PER_PAGE = 500  # Gmail API maximum
```

---

## 4. Long Method: _parse_credit_card_purchase

**Severity:** Medium  
**Category:** Long Method

### Description
The `_parse_credit_card_purchase` method in `HeyBancoParser` is 67 lines long and handles multiple responsibilities: validation, amount parsing, description extraction, date parsing, and card type determination.

### Location
- `core/parsers/hey_banco.py` (lines 277-339)

### Impact
- Difficult to test individual parts
- Harder to understand at a glance
- Multiple reasons to change (violates Single Responsibility Principle)

### Suggested Fix
Break down into smaller methods:
- `_extract_amount(text)` 
- `_extract_merchant(text)`
- `_extract_transaction_date(text)`
- `_determine_card_type(text)`

---

## 5. Feature Envy: Return Type in ParserHelper

**Severity:** Low  
**Category:** Design Smell

### Description
The `get_parser_for_email` method returns a union of specific parser types instead of the base `BaseBankParser` type, creating tight coupling.

### Location
- `core/parsers/parser_helper.py` (lines 33-51)

### Impact
- Every time a new parser is added, the return type annotation must be updated
- Violates Open/Closed Principle
- Creates unnecessary coupling to concrete implementations

### Suggested Fix
Change return type to base class:
```python
def get_parser_for_email(from_header: str) -> BaseBankParser | None:
```

---

## 6. Missing Explicit Return Statement

**Severity:** Low  
**Category:** Code Clarity

### Description
The `get_parser_for_email` method doesn't have an explicit `return None` at the end.

### Location
- `core/parsers/parser_helper.py` (line 51)

### Impact
- Implicit behavior is less clear
- May confuse developers unfamiliar with Python's implicit None return

### Suggested Fix
Add explicit return statement:
```python
return PARSERS.get(bank)
return None  # No matching parser found
```

---

## 7. Dead Code: PAYPAL Bank Definition

**Severity:** Low  
**Category:** Dead Code

### Description
`SupportedBanks.PAYPAL` is defined in the enum and has email addresses configured, but the PayPalParser is commented out.

### Locations
- `constants/banks.py` (line 22) - PAYPAL enum value defined
- `constants/banks.py` (line 38) - PAYPAL emails configured
- `core/parsers/parser_helper.py` (line 24) - PayPalParser commented out

### Impact
- Confusion about whether PayPal is actually supported
- Unused constants taking up space
- May cause issues if someone tries to use PayPal

### Suggested Fix
Either:
1. Remove PAYPAL from constants if not ready, or
2. Implement PayPalParser if support is intended

---

## 8. Variable Shadowing Bug: Duplicate Assignment

**Severity:** High  
**Category:** Bug

### Description
Line 78 in `hey_banco.py` has a duplicate assignment: `amount = amount = float(...)`, which is clearly a mistake.

### Location
- `core/parsers/hey_banco.py` (line 78)

### Code
```python
amount = amount = float(amount_match.group(1).replace(",", ""))
```

### Impact
- This is a clear typo/bug
- While functionally it works, it indicates careless coding
- May confuse code reviewers and maintainers

### Suggested Fix
```python
amount = float(amount_match.group(1).replace(",", ""))
```

---

## 9. Double Session Commit

**Severity:** Medium  
**Category:** Performance / Design Issue

### Description
The `save_transaction` method commits the database session twice: once for the bank (line 33) and once for the transaction (line 50).

### Location
- `core/services/transaction_service.py` (lines 33, 50)

### Impact
- Inefficient: Two database commits when one would suffice
- Breaks transaction atomicity partially
- The bank commit happens before the transaction is validated

### Suggested Fix
Commit only once at the end, or rely on the context manager's automatic commit:
```python
bank = Bank(name=transaction.bank_name)
session.add(bank)
session.flush()  # Get ID without committing
# ... rest of code
# Let context manager handle the single commit
```

---

## 10. Logging Bug: Duplicate category_id

**Severity:** Low  
**Category:** Bug

### Description
Line 60 logs `category_id` twice instead of logging both `category_id` and `subcategory_id`.

### Location
- `core/services/transaction_service.py` (line 60)

### Code
```python
logger.info(
    "Transaction added [ID: %s] | %s | %s | %s | Category: %s | Subcategory: %s",
    tx.transaction_id,
    tx.amount,
    tx.date,
    tx.description,
    tx.category_id,
    tx.category_id,  # Should be tx.subcategory_id
)
```

### Impact
- Incorrect logging output
- Subcategory information is never logged
- Makes debugging harder

### Suggested Fix
```python
tx.category_id,
tx.subcategory_id,
```

---

## 11. Data Clump: email_message Dictionary

**Severity:** Medium  
**Category:** Data Clump

### Description
The `email_message` dictionary is passed around with keys accessed inconsistently. Different parsers access different combinations of keys (`body_html`, `body_plain`, `subject`, `date`).

### Locations
- Multiple parser files access `email_message` with varying patterns
- No clear data contract or validation

### Impact
- Unclear what keys are guaranteed to exist
- Prone to KeyError if dict structure changes
- Difficult to refactor

### Suggested Fix
Create an `EmailMessage` dataclass or Pydantic model:
```python
@dataclass
class EmailMessage:
    id: str
    subject: str
    from_address: str
    date: str
    body_plain: str = ""
    body_html: str = ""
```

---

## 12. Class Variable as Instance Variable

**Severity:** Low  
**Category:** Design Issue

### Description
`Database.engine` is defined as a class variable (line 29) but is used as an instance variable, which could lead to unexpected sharing between instances.

### Location
- `database/database.py` (line 29)

### Code
```python
class Database:
    engine = None  # Class variable
    
    def __init__(self, db_url="sqlite:///expenses.db"):
        self.engine = create_engine(...)  # Assigned as instance variable
```

### Impact
- Confusing: Appears to be class variable but used as instance
- Could cause bugs if multiple Database instances are created with different URLs
- Not following Python best practices

### Suggested Fix
Remove the class variable declaration:
```python
class Database:
    def __init__(self, db_url="sqlite:///expenses.db"):
        self.engine = create_engine(...)
```

---

## 13. Inconsistent Error Handling

**Severity:** Medium  
**Category:** Error Handling

### Description
Error handling is inconsistent across the codebase. Some methods return `None` on error, some log and continue, and error handling patterns vary.

### Examples
- `_decode_payload()` returns placeholder string on error
- Parser methods return `None` on parsing failure
- `save_transaction()` returns `None` or int
- Some exceptions are caught broadly, others specifically

### Impact
- Unclear error handling contract
- Difficult to debug issues
- May hide important errors
- Inconsistent user experience

### Suggested Fix
Define a consistent error handling strategy:
1. Use custom exceptions for different error types
2. Document what each method returns on failure
3. Consider using Result types or Optional types consistently

---

## 14. Inconsistent Body Selection Logic

**Severity:** Medium  
**Category:** Code Inconsistency / Bug

### Description
Different parsers have inconsistent logic for choosing between `body_html` and `body_plain`.

### Locations
- `hey_banco.py` (lines 46-49): Prefers HTML, falls back to plain
- `rappi.py` (lines 52-55): Fetches plain twice (bug)
- `nubank.py` (lines 63-64): Only uses plain
- `banorte.py` (lines 80-83): Prefers HTML, falls back to plain

### Impact
- Inconsistent behavior across parsers
- The Rappi parser has a clear bug (fetches body_plain twice)
- Makes testing harder due to varying assumptions

### Suggested Fix
Implement a consistent body selection strategy, possibly in the base parser class.

---

## Summary

**Total Issues:** 14  
**High Severity:** 1  
**Medium Severity:** 8  
**Low Severity:** 5

### Priority Recommendations
1. **Fix Bug #8** (Variable shadowing) - Quick win, clear bug
2. **Fix Bug #10** (Logging bug) - Quick win, clear bug  
3. **Fix Bug #14** (Rappi body selection) - Quick win, clear bug
4. **Refactor #1** (Duplicate month mappings) - High impact on maintainability
5. **Refactor #2** (Duplicate date normalization) - Improves HeyBancoParser
6. **Fix #9** (Double session commit) - Performance and design improvement
7. Address remaining issues based on development priorities

---

*Generated: 2026-01-13*  
*Repository: javrr-ui/expense-tracker*
