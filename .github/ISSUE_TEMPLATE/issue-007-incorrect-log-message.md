# Bug: Incorrect Log Message in TransactionService

## Type
Bug

## Severity
Low

## Description
The log message in `TransactionService.save_transaction()` incorrectly logs `tx.category_id` twice instead of logging both `tx.category_id` and `tx.subcategory_id`.

## Location
`core/services/transaction_service.py:54-61`

## Current Code
```python
logger.info(
    "Transaction added [ID: %s] | %s | %s | %s | Category: %s | Subcategory: %s",
    tx.transaction_id,
    tx.amount,
    tx.date,
    tx.description,
    tx.category_id,
    tx.category_id,  # ← Should be tx.subcategory_id
)
```

## Impact
- Misleading log output
- Makes debugging category/subcategory assignments more difficult
- Functional impact: Low (logging only)

## Proposed Solution
Fix the last parameter to use the correct attribute:

```python
logger.info(
    "Transaction added [ID: %s] | %s | %s | %s | Category: %s | Subcategory: %s",
    tx.transaction_id,
    tx.amount,
    tx.date,
    tx.description,
    tx.category_id,
    tx.subcategory_id,  # ← Fixed
)
```

## Effort Estimate
Trivial (2 minutes)

## Related Files
- `core/services/transaction_service.py`
