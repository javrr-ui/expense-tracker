# Code Smell: Too Many Local Variables in Banorte Parser Method

## Type
Complexity

## Severity
Low

## Description
The `_parse_outgoing_transfer()` method in `BanorteParser` has 18 local variables (limit is 15), which suggests the method is doing too much and could benefit from refactoring. This is flagged by pylint as R0914 (too-many-locals).

## Location
`core/parsers/banorte.py:91` - `_parse_outgoing_transfer()` method

## Current Code Structure
The method extracts amount, description, time, and date using multiple regex matches, with each extraction creating several intermediate variables.

## Impact
- Pylint warning R0914 (too-many-locals)
- Method is doing too much (parsing, regex matching, date normalization)
- Difficult to understand and maintain
- High cognitive complexity

## Proposed Solution
1. Extract date parsing logic into a separate helper method
2. Extract regex pattern matching into dedicated methods
3. Consider creating a data structure to hold intermediate parsing results

## Example Solution
```python
class BanorteParser(BaseBankParser):
    # Move patterns to class level
    AMOUNT_PATTERN = re.compile(
        r"Importe: </td>\s*<td nowrap=\"nowrap\">\s*\$([\d,]+\.\d{2}) MN\s*</td>"
    )
    DESCRIPTION_PATTERN = re.compile(
        r"Operación: </td>\s*<td align=\"left\" nowrap=\"nowrap\">\s*(.*?)\s*</td>"
    )
    # ... other patterns ...
    
    def _parse_outgoing_transfer(self, text: str, email_id: str) -> Transaction | None:
        """Parse an outgoing SPEI transfer from the email body."""
        
        # Extract data using helper methods
        amount = self._extract_amount(text)
        description = self._extract_description(text)
        datetime_obj = self._extract_datetime(text)
        
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
    
    def _extract_amount(self, text: str) -> float:
        """Extract transaction amount from email text."""
        match = self.AMOUNT_PATTERN.search(text)
        if match:
            return float(match.group(1).replace(",", ""))
        return 0.0
    
    def _extract_description(self, text: str) -> str:
        """Extract transaction description from email text."""
        match = self.DESCRIPTION_PATTERN.search(text)
        return match.group(1) if match else ""
    
    def _extract_datetime(self, text: str) -> datetime | None:
        """Extract and parse transaction date and time."""
        # Date and time extraction logic here
        # This reduces variables in the main method
        pass
```

## Effort Estimate
Medium (3-4 hours)

## Related Files
- `core/parsers/banorte.py`

## Additional Notes
This refactoring would also improve testability, as individual extraction methods could be tested independently.
