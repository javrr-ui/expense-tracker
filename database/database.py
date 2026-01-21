"""SQLite database interface for the expense tracker.

This module defines the Database class, which manages the SQLite database
used to store transactions, sources (banks), categories, and subcategories.

It ensures the schema is created on initialization, supports context manager
usage, and provides safe methods for inserting transactions while handling
duplicates and errors.
"""

import logging

from contextlib import contextmanager
from sqlmodel import create_engine, SQLModel, Session

from models.bank import Bank
from models.category import Category
from models.subcategory import Subcategory
from models.transaction import Transaction
from models.account import Account
from models.account_type import AccountType

# These imports ensure SQLModel discovers all table definitions
__all__ = [
    "Database",
    "Bank",
    "Category",
    "Subcategory",
    "Transaction",
    "Account",
    "AccountType",
]


logger = logging.getLogger("expense_tracker")


class Database:
    """SQLite database handler for storing and managing financial transactions.

    Creates and maintains the required tables (sources, categories, subcategories,
    transactions) with proper foreign key constraints.

    Supports context manager protocol for safe connection handling.
    """

    engine = None

    def __init__(self, db_url="sqlite:///expenses.db"):
        """Initialize database connection and ensure schema exists.

        Args:
            db_name: URL to the  database . Defaults to "sqlite:///expenses.db".

        Raises:
            sqlite3.Error: If connection or schema creation fails.
        """
        try:
            self.engine = create_engine(
                url=db_url,
                echo=False,
            )

            SQLModel.metadata.create_all(self.engine)
            logger.info("Database initialized: %s", db_url)
        except Exception as e:
            logger.error("Database initialization failed: %s", e)
            raise

    @contextmanager
    def session(self):
        """Context manager that yields a Session and handles commit/rollback."""
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error("Database session failed: %s", e)
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """Close the database connection."""
        self.engine.dispose()
        logger.info("Database engine disposed")
