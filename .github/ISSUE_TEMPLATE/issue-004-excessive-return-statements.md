# Code Smell: Too Many Return Statements in Validation Method

## Type
Complexity / Poor Design

## Severity
Medium

## Description
The `is_transaction_not_valid_or_email_not_supported()` method in `HeyBancoParser` has 9 return statements (limit is 6), making the function difficult to read and maintain. This is flagged by pylint as R0911 (too-many-return-statements).

## Location
`core/parsers/hey_banco.py:341` - `is_transaction_not_valid_or_email_not_supported()` method

## Current Code
```python
def is_transaction_not_valid_or_email_not_supported(self, text: str) -> bool:
    """Filter out failed, blocked, or irrelevant notifications."""
    rejected_match = re.search(
        r"La compra que realizaste fue rechazada por Fondos Insuficientes", text
    )
    if rejected_match:
        return True

    freezed_debit_card_match = re.search(
        r"¡Has bloqueado tu tarjeta de débito", text
    )
    if freezed_debit_card_match:
        return True

    # ... 7 more similar patterns ...
    
    return False
```

## Impact
- Pylint warning R0911 (too-many-return-statements)
- Difficult to read and understand the validation logic
- Hard to maintain and extend with new patterns
- Each pattern requires separate regex compilation and matching

## Proposed Solution
Refactor to use a list of patterns and check them in a loop:

## Example Solution
```python
def is_transaction_not_valid_or_email_not_supported(self, text: str) -> bool:
    """Filter out failed, blocked, or irrelevant notifications."""
    
    # List of patterns that indicate invalid/unsupported transactions
    invalid_patterns = [
        r"La compra que realizaste fue rechazada por Fondos Insuficientes",
        r"¡Has bloqueado tu tarjeta de débito",
        r"El pago que intentaste hacer hace un momento no ha sido procesado\.",
        r"Recuperación de usuario\.",
        r"No se ha podido realizar tu transferencia nacional\.",
        r"La compra que realizaste fue rechazada por CVV Inválido",
        r"Tu tarjeta virtual tiene nueva fecha de vencimiento",
        r"Tu fecha de vencimiento se renovará",
    ]
    
    # Check if any pattern matches
    for pattern in invalid_patterns:
        if re.search(pattern, text):
            return True
    
    return False
```

## Alternative Solution
For better performance, compile patterns once at class initialization:

```python
class HeyBancoParser(BaseBankParser):
    # Class-level compiled patterns
    INVALID_TRANSACTION_PATTERNS = [
        re.compile(r"La compra que realizaste fue rechazada por Fondos Insuficientes"),
        re.compile(r"¡Has bloqueado tu tarjeta de débito"),
        # ... rest of patterns ...
    ]
    
    def is_transaction_not_valid_or_email_not_supported(self, text: str) -> bool:
        """Filter out failed, blocked, or irrelevant notifications."""
        return any(pattern.search(text) for pattern in self.INVALID_TRANSACTION_PATTERNS)
```

## Effort Estimate
Small (1 hour)

## Related Files
- `core/parsers/hey_banco.py`
