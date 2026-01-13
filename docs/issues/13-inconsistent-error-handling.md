# Code Smell: Inconsistent Error Handling

**Labels:** `code-quality`, `refactoring`, `medium-priority`, `error-handling`  
**Type:** Error Handling Inconsistency

## Description

Error handling is inconsistent throughout the codebase. Different methods use different patterns for handling and reporting errors, making it difficult to understand the error handling contract and debug issues.

## Examples of Inconsistency

### 1. Return Values on Error

```python
# Some methods return None
def _parse_credit_card_payment(self, text, email_id) -> Transaction | None:
    # ...
    if amount_match:
        try:
            amount = float(amount_match.group(1).replace(",", ""))
        except ValueError:
            logger.error("Failed to parse amount: %s", amount_match.group(1))
            return None  # ← Returns None on error

# Some methods return placeholder values
def _decode_payload(part):
    try:
        # ... decoding logic
    except (TypeError, ValueError, AttributeError) as e:
        logger.error("Error decoding email payload: %s", e)
        return "[Error al decodificar el cuerpo del email]"  # ← Returns placeholder

# Some return Optional[int]
def save_transaction(self, transaction: TransactionCreate) -> Optional[int]:
    try:
        # ...
        return tx.transaction_id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(...)
        return None  # ← Returns None on error
```

### 2. Exception Catching Patterns

```python
# Some catch broad exceptions
except Exception as e:
    logger.error("An error occurred: %s", e, exc_info=True)
    raise

# Some catch specific exceptions
except (ValueError, TypeError, OverflowError) as e:
    logger.error("Failed to parse date: %s -> %s", date_str, e)

# Some catch multiple specific exceptions separately
except SQLAlchemyError as e:
    # ...
except ValueError as e:
    # ...
```

### 3. Logging Patterns

```python
# Some include exc_info
logger.error("An error occurred: %s", e, exc_info=True)

# Some don't
logger.error("Failed to parse amount: %s", amount_match.group(1))

# Some log and continue, others log and return/raise
```

## Impact

- **Unclear Contract:** Difficult to know what to expect on error
- **Debugging Difficulty:** Inconsistent error information
- **Error Hiding:** Some errors might be silently swallowed
- **User Experience:** No consistent error handling for users
- **Testing:** Hard to test error conditions consistently

## Proposed Solution

Define a consistent error handling strategy:

### 1. Create Custom Exception Types

```python
# core/exceptions.py
class ExpenseTrackerError(Exception):
    """Base exception for expense tracker."""
    pass

class ParsingError(ExpenseTrackerError):
    """Error parsing email content."""
    pass

class DatabaseError(ExpenseTrackerError):
    """Error interacting with database."""
    pass

class AuthenticationError(ExpenseTrackerError):
    """Error authenticating with Gmail."""
    pass
```

### 2. Define Error Handling Patterns

```python
# For parser methods: Return None on failure, log warning
def _parse_credit_card_payment(self, text, email_id) -> Transaction | None:
    try:
        amount = self._extract_amount(text)
        if amount is None:
            logger.warning("Could not extract amount from email %s", email_id)
            return None
        # ... continue parsing
    except ParsingError as e:
        logger.warning("Failed to parse credit card payment: %s", e)
        return None

# For service methods: Return Result type or raise exception
from typing import Union, TypeVar, Generic

T = TypeVar('T')

class Result(Generic[T]):
    """Result type for operations that can fail."""
    
    def __init__(self, value: T | None = None, error: Exception | None = None):
        self.value = value
        self.error = error
    
    @property
    def is_success(self) -> bool:
        return self.error is None
    
    @property
    def is_failure(self) -> bool:
        return self.error is not None

def save_transaction(self, transaction: TransactionCreate) -> Result[int]:
    try:
        # ... save logic
        return Result(value=tx.transaction_id)
    except SQLAlchemyError as e:
        logger.error("Database error: %s", e, exc_info=True)
        return Result(error=DatabaseError(f"Failed to save transaction: {e}"))
```

### 3. Document Error Handling in Docstrings

```python
def parse(self, email_message, email_id: str) -> Transaction | None:
    """Parse an email message to extract a transaction.
    
    Args:
        email_message: The parsed email message dict
        email_id: The unique identifier of the email
        
    Returns:
        Transaction object if parsing succeeds, None otherwise.
        
    Note:
        This method logs warnings for parsing failures and returns None
        rather than raising exceptions. This allows the main loop to
        continue processing other emails even if one fails.
    """
```

## Recommended Strategy

1. **Parser Methods:** Return `None` on failure, log at WARNING level
2. **Service Methods:** Use Result type or raise custom exceptions
3. **Main Loop:** Catch and log exceptions, continue processing
4. **Critical Errors:** Let exceptions propagate (auth, database connection)
5. **Logging:** Always use `exc_info=True` for ERROR level

## Acceptance Criteria

- [ ] Define custom exception types
- [ ] Document error handling strategy in CONTRIBUTING.md
- [ ] Update docstrings to document error behavior
- [ ] Consider implementing Result type for service layer
- [ ] Add consistent logging patterns
- [ ] Update tests to verify error handling

## Priority

**Medium** - While the current code works, inconsistent error handling makes maintenance and debugging harder. This should be addressed as part of a refactoring effort.

## Related Issues

- #4 (Long method) - Refactoring provides opportunity to improve error handling
- #11 (Data clump) - New models can include validation and better error handling
