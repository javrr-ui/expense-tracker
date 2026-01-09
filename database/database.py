"""SQLite database interface for the expense tracker.

This module defines the Database class, which manages the SQLite database
used to store transactions, sources (banks), categories, and subcategories.

It ensures the schema is created on initialization, supports context manager
usage, and provides safe methods for inserting transactions while handling
duplicates and errors.
"""

import logging
import sqlite3

from models.transaction import Transaction

logger = logging.getLogger("expense_tracker")


class Database:
    """SQLite database handler for storing and managing financial transactions.

    Creates and maintains the required tables (sources, categories, subcategories,
    transactions) with proper foreign key constraints.

    Supports context manager protocol for safe connection handling.
    """

    def __init__(self, db_name="expenses.db"):
        """Initialize database connection and ensure schema exists.

        Args:
            db_name: Path to the SQLite database file. Defaults to "expenses.db".

        Raises:
            sqlite3.Error: If connection or schema creation fails.
        """
        try:
            self.conn = sqlite3.connect(db_name)
            self.cursor = self.conn.cursor()
            logger.info("Successful connection to the database: %s", db_name)

            self.cursor.execute("PRAGMA foreign_keys = ON;")
            logger.debug("Foreign key support enabled")

            self.cursor.executescript(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS subcategories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    UNIQUE( name, category_id)
                );     
                        
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT UNIQUE,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    source_id INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
                    description TEXT,
                    category_id INTEGER,
                    subcategory_id INTEGER,
                    
                    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE RESTRICT,
                    FOREIGN KEY (category_id) REFERENCES categories(id),
                    FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
                );
                        """
            )
            self.conn.commit()
            logger.info("Database tables ensured")
        except sqlite3.Error as e:
            logger.error("Database error: %s", e)
            raise

    def close(self):
        """Close the database connection."""
        self.conn.close()
        logger.info("Database connection closed")

    def __enter__(self):
        """Support context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support context manager exit — ensure connection is closed."""
        self.close()

    def add_transaction(self, transaction: Transaction) -> int | None:
        """
        Add a new transaction to the database

        Args:
            date (str): Format 'YYYY-MM-DD HH:MM:SS'
            amount (float): Positive float number
            email_id (str): The email ID associated with the transaction
            description (str, optional): Defaults to None.
            category_name (str, optional): Defaults to None.
            subcategory_name (str, optional): Defaults to None.
        Returns:
            int: The ID of the new transaction
        """

        try:
            category_id = None
            subcategory_id = None

            self.cursor.execute(
                "INSERT OR IGNORE INTO sources (name) VALUES (?)", (transaction.source,)
            )
            self.cursor.execute(
                "SELECT id FROM sources WHERE name = ?", (transaction.source,)
            )
            source_id = self.cursor.fetchone()[0]

            self.cursor.execute(
                """
                INSERT INTO transactions
                (date, amount, description, category_id, subcategory_id, email_id, source_id, type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    transaction.date,
                    transaction.amount,
                    transaction.description,
                    category_id,
                    subcategory_id,
                    transaction.email_id,
                    source_id,
                    transaction.type,
                ),
            )

            transaction_id = self.cursor.lastrowid
            self.conn.commit()

            logger.info(
                "Transaction added [ID: %s] | %s | %s | %s | Category: %s | Subcategory: %s",
                transaction_id,
                transaction.amount,
                transaction.date,
                transaction.description,
                transaction.category_name,
                transaction.subcategory_name,
            )

            return transaction_id
        except sqlite3.IntegrityError as e:
            if (
                transaction.email_id
                and "UNIQUE constraint failed: transactions.email_id" in str(e)
            ):
                logger.warning(
                    "Skipped duplicate transaction (email_id: %s)", transaction.email_id
                )
                self.conn.rollback()
                return None  # or raise if you prefer strict mode

            logger.error("Integrity error adding transaction: %s", e)
            logger.error(
                "Failed data - date: %s, amount: %s, email_id: %s, source: %s, type: %s",
                transaction.date,
                transaction.amount,
                transaction.email_id,
                transaction.source,
                transaction.type,
            )
            self.conn.rollback()
            return None
        except sqlite3.Error as e:
            logger.error("Database error adding transaction: %s", e)
            self.conn.rollback()
            raise
