# Code Smell: Duplicate TransactionCreate Instantiation Pattern

## Type
Code Duplication

## Severity
Low

## Description
Every parser method that creates a transaction uses nearly identical `TransactionCreate(...)` instantiation code with the same parameter order and many `None` values. This creates significant code duplication across all parser methods.

## Location
Found in multiple methods across all parser files:
- `core/parsers/hey_banco.py` (lines 100-111, 180-191, 264-275, 328-339)
- `core/parsers/nubank.py` (lines 106-116, 134-144, 162-172)
- `core/parsers/banorte.py` (lines 151-162)
- `core/parsers/rappi.py` (lines 103-112)

## Current Code Pattern
```python
return TransactionCreate(
    bank_name=self.bank_name,
    email_id=email_id,
    date=datetime_obj,
    amount=amount,
    description=description,
    merchant=None,
    reference=None,
    status="",
    type="expense",
)
```

## Impact
- Significant code duplication (detected by pylint R0801)
- Changes to the Transaction model require updates in many places
- Verbose and repetitive code reduces readability
- Increases risk of inconsistencies

## Proposed Solution
1. Add a helper method to `BaseBankParser` that creates `TransactionCreate` instances with sensible defaults
2. Reduce boilerplate by leveraging default values in `TransactionCreate`
3. Allow parsers to override only the values they need

## Example Solution
```python
# In core/parsers/base_parser.py
def create_transaction(
    self,
    email_id: str,
    amount: float,
    transaction_type: Literal["expense", "income"],
    date: datetime | None = None,
    description: str = "",
    merchant: str | None = None,
    reference: str | None = None,
    status: str = "",
) -> TransactionCreate:
    """Create a TransactionCreate instance with bank name pre-filled."""
    return TransactionCreate(
        bank_name=self.bank_name,
        email_id=email_id,
        date=date,
        amount=amount,
        description=description,
        type=transaction_type,
        merchant=merchant,
        reference=reference,
        status=status,
    )

# Usage in parsers becomes:
return self.create_transaction(
    email_id=email_id,
    amount=amount,
    transaction_type="expense",
    date=datetime_obj,
    description=description,
)
```

## Effort Estimate
Small (2-3 hours)

## Related Files
- `core/parsers/base_parser.py`
- `core/parsers/hey_banco.py`
- `core/parsers/nubank.py`
- `core/parsers/banorte.py`
- `core/parsers/rappi.py`
