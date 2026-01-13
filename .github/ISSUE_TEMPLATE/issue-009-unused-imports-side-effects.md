# Code Smell: Unused Imports with Side Effects in Database Module

## Type
Code Quality / Import Issue

## Severity
Low

## Description
The `Database.__init__()` method imports model classes (`Bank`, `Category`, `Subcategory`, `Transaction`) that appear unused but are actually required for SQLModel to discover the table schemas. This triggers pylint warnings W0611 (unused-import) and C0415 (import-outside-toplevel).

## Location
`database/database.py:46-49`

## Current Code
```python
def __init__(self, db_url="sqlite:///expenses.db"):
    try:
        self.engine = create_engine(
            url=db_url,
            echo=False,
        )

        from models.bank import Bank
        from models.category import Category
        from models.subcategory import Subcategory
        from models.transaction import Transaction

        SQLModel.metadata.create_all(self.engine)
        logger.info("Database initialized: %s", db_url)
```

## Impact
- Pylint warnings: C0415 (import-outside-toplevel) and W0611 (unused-import)
- Code appears to have unused imports, confusing maintainers
- The imports are actually needed for SQLModel's metadata discovery
- Not a functional bug, but a code quality issue

## Proposed Solution

**Option 1: Add noqa comments to suppress warnings**
```python
from models.bank import Bank  # noqa: F401 - Required for SQLModel metadata
from models.category import Category  # noqa: F401
from models.subcategory import Subcategory  # noqa: F401
from models.transaction import Transaction  # noqa: F401
```

**Option 2: Store references to prevent "unused" warnings**
```python
from models.bank import Bank
from models.category import Category
from models.subcategory import Subcategory
from models.transaction import Transaction

# Register models for SQLModel metadata discovery
_models = (Bank, Category, Subcategory, Transaction)
```

**Option 3: Move imports to module level and improve structure**
```python
# At top of database.py
from models.bank import Bank
from models.category import Category
from models.subcategory import Subcategory
from models.transaction import Transaction

# These imports ensure SQLModel discovers all table definitions
__all__ = ["Database", "Bank", "Category", "Subcategory", "Transaction"]
```

## Recommended Solution
Option 3 - Move imports to module level. This is the most Pythonic approach and makes the intent clear.

## Effort Estimate
Small (30 minutes)

## Related Files
- `database/database.py`

## Additional Notes
This is a common pattern with ORMs that use metaclass-based model discovery. The solution should make the intent clear to both humans and linters.
