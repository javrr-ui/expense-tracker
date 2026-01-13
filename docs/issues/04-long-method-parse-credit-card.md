# Code Smell: Long Method (_parse_credit_card_purchase)

**Labels:** `code-quality`, `refactoring`, `medium-priority`  
**Type:** Long Method

## Description

The `_parse_credit_card_purchase` method in `HeyBancoParser` is 67 lines long and handles multiple responsibilities, making it difficult to test, understand, and maintain.

## Location

- `core/parsers/hey_banco.py` (lines 277-339)

## Current Issues

The method does too much:
1. Validates transaction (calls another method)
2. Extracts amount with regex and parsing
3. Extracts merchant/description
4. Extracts and parses date
5. Determines card type (credit vs debit)
6. Constructs Transaction object

## Impact

- **Testing Difficulty:** Cannot easily test individual extraction logic
- **Readability:** Hard to understand the full flow at a glance
- **Maintainability:** Changes to one aspect affect the entire method
- **Reusability:** Cannot reuse extraction logic elsewhere
- **Violations:** Breaks Single Responsibility Principle

## Proposed Solution

Break down into focused, testable methods:

```python
def _parse_credit_card_purchase(self, text: str, email_id: str) -> Transaction | None:
    """Parse a debit or credit card purchase alert."""
    if self.is_transaction_not_valid_or_email_not_supported(text):
        return None
    
    amount = self._extract_purchase_amount(text)
    if amount is None:
        return None
        
    merchant = self._extract_merchant_name(text)
    transaction_date = self._extract_transaction_date(text)
    card_type = self._determine_card_type(text)
    
    description = f"{merchant} {card_type}" if card_type else merchant
    
    return TransactionCreate(
        bank_name=self.bank_name,
        email_id=email_id,
        date=transaction_date,
        amount=amount,
        description=description,
        merchant=merchant,
        reference=None,
        status="",
        type="expense",
    )

def _extract_purchase_amount(self, text: str) -> float | None:
    """Extract purchase amount from card purchase email."""
    amount_match = re.search(
        r"Cantidad:[\s\S]*?<h4[^>]*>\s*\$?([\d,]+\.\d{2})\s*</h4>", text
    )
    if not amount_match:
        return None
        
    try:
        return float(amount_match.group(1).replace(",", ""))
    except ValueError:
        logger.error("Failed to parse amount: %s", amount_match.group(1))
        return None

def _extract_merchant_name(self, text: str) -> str:
    """Extract merchant/store name from card purchase email."""
    description_match = re.search(
        r"Comercio:[\s\S]*?<h4[^>]*>\s*([^<]+?)\s*</h4>", text
    )
    return description_match.group(1).strip() if description_match else ""

def _extract_transaction_date(self, text: str) -> datetime | None:
    """Extract transaction date from card purchase email."""
    date_match = re.search(
        r"Fecha y hora de la transacci&oacute;n:[\s\S]*?<h4[^>]*>\s*"
        r"(\d{1,2}/\d{1,2}/\d{4}\s*-\s*\d{2}:\d{2}\s*hrs)"
        r"\s*</h4>",
        text,
    )
    if not date_match:
        return None
        
    date_str = date_match.group(1)
    cleaned = date_str.replace("hrs", "").strip()
    try:
        return date_parser(cleaned, dayfirst=True)
    except (ValueError, TypeError, OverflowError) as e:
        logger.error("Failed to parse date: %s -> %s", date_str, e)
        return None

def _determine_card_type(self, text: str) -> str:
    """Determine if purchase was with credit or debit card."""
    card_type_match = re.search(
        r"con tu <b>(Credito|Debito|Crédito|Débito|Cr&eacute;dito|D&eacute;bito)</b>",
        text,
    )
    if not card_type_match:
        return ""
        
    card = unidecode(card_type_match.group(1).strip().lower())
    
    if card == "debito":
        return "debit_card_purchase"
    elif card == "credito":
        return "credit_card_purchase"
    
    return ""
```

## Acceptance Criteria

- [ ] Extract `_extract_purchase_amount()` method
- [ ] Extract `_extract_merchant_name()` method
- [ ] Extract `_extract_transaction_date()` method
- [ ] Extract `_determine_card_type()` method
- [ ] Update `_parse_credit_card_purchase()` to use new methods
- [ ] Reduce main method to ~20 lines (orchestration only)
- [ ] Add unit tests for each extraction method
- [ ] Verify all existing functionality still works

## Benefits

- Each method has a single, clear responsibility
- Easier to test individual components
- Better error handling at each step
- More reusable code
- Clearer method names document the process
