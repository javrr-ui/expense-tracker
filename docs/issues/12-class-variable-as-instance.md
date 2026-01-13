# Code Smell: Class Variable Used as Instance Variable

**Labels:** `code-quality`, `refactoring`, `low-priority`, `design`  
**Type:** Design Issue

## Description

The `Database` class defines `engine` as a class variable (line 29) but then assigns it as an instance variable in `__init__`. This is confusing and could lead to unexpected behavior if multiple `Database` instances are created.

## Location

- `database/database.py` (lines 29, 41)

## Current Code

```python
class Database:
    """SQLite database handler for storing and managing financial transactions."""

    engine = None  # ← Class variable declaration

    def __init__(self, db_url="sqlite:///expenses.db"):
        """Initialize database connection and ensure schema exists."""
        try:
            self.engine = create_engine(  # ← Assigned as instance variable
                url=db_url,
                echo=False,
            )
            # ...
```

## Impact

- **Confusing:** Appears to be a class variable but is actually used as instance variable
- **Misleading:** Suggests engine might be shared across instances
- **Best Practice Violation:** Not following Python conventions
- **Potential Bugs:** Could cause issues if:
  - Multiple Database instances created with different URLs
  - Code tries to access Database.engine directly
  - Inheritance is used

## Example of Potential Issue

```python
# This could be confusing
db1 = Database("sqlite:///db1.db")
db2 = Database("sqlite:///db2.db")

# What is Database.engine? It could be:
# - None (the class variable)
# - db2.engine (if last assignment to class var)
# - Undefined behavior
```

## Proposed Solution

Remove the class variable declaration and use only instance variables:

```python
class Database:
    """SQLite database handler for storing and managing financial transactions.

    Creates and maintains the required tables (sources, categories, subcategories,
    transactions) with proper foreign key constraints.

    Supports context manager protocol for safe connection handling.
    """

    def __init__(self, db_url="sqlite:///expenses.db"):
        """Initialize database connection and ensure schema exists.

        Args:
            db_url: URL to the database. Defaults to "sqlite:///expenses.db".

        Raises:
            sqlite3.Error: If connection or schema creation fails.
        """
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
        except Exception as e:
            logger.error("Database initialization failed: %s", e)
            raise
```

## Alternative Solution

If the intent was to share a single engine across instances (not recommended for SQLite), properly implement it as a singleton pattern or class method.

## Acceptance Criteria

- [ ] Remove `engine = None` class variable declaration
- [ ] Verify engine is properly initialized as instance variable
- [ ] Test with single Database instance
- [ ] Test with multiple Database instances (if applicable)
- [ ] Ensure no code accesses `Database.engine` directly
- [ ] Run all tests to ensure no regressions

## Priority

**Low** - This doesn't cause functional issues in the current codebase since only one Database instance is typically created. However, it's a code smell that should be addressed for clarity and maintainability.

## Additional Context

The current usage in `main.py` creates only one Database instance, so this doesn't cause actual problems. However, fixing it improves code quality and prevents future issues.
