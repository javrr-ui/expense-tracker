# Bug: Logging Duplicate category_id

**Labels:** `bug`, `low-priority`, `easy-fix`  
**Type:** Code Error

## Description

Line 60 in `transaction_service.py` logs `category_id` twice instead of logging both `category_id` and `subcategory_id`. The subcategory information is never logged.

## Location

- `core/services/transaction_service.py` (line 60)

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

- **Incorrect Logging:** Subcategory information never appears in logs
- **Debugging:** Makes it harder to debug category/subcategory issues
- **Misleading:** Log message claims to show subcategory but shows category twice

## Proposed Solution

Fix the typo by changing the last parameter:

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

## Acceptance Criteria

- [ ] Change second `tx.category_id` to `tx.subcategory_id`
- [ ] Test that logging works correctly
- [ ] Verify log output shows correct values

## Priority

**Low** - This is a minor bug that only affects logging output. However, it's a very easy fix that should be included in any PR touching this file.

## Related Issues

- #9 (Double session commit) - Same method, can be fixed together
