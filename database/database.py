import sqlite3
import logging 

logger = logging.getLogger("expense_tracker")

class Database:
    def __init__(self, db_name='expenses.db'):
        try:
            self.conn = sqlite3.connect(db_name)
            self.cursor = self.conn.cursor()
            logger.info(f"Successful connection to the database: {db_name}")
            
            self.cursor.execute('PRAGMA foreign_keys = ON;')
            logger.debug("Foreign key support enabled")
            
            self.cursor.executescript('''
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
                        ''')
            self.conn.commit()
            logger.info("Database tables ensured")
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
        
    def close(self):
        self.conn.close()
        logger.info("Database connection closed")
        
    def __enter__(self):
        return self
    
    def add_transaction(self, date: str, amount: float, email_id: str, source: str, type: str, description: str = None,category_name: str = None, subcategory_name: str = None):
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
            
            self.cursor.execute("INSERT OR IGNORE INTO sources (name) VALUES (?)", (source,))
            self.cursor.execute("SELECT id FROM sources WHERE name = ?", (source,))
            source_id = self.cursor.fetchone()[0]
            
            self.cursor.execute("""
                INSERT INTO transactions
                (date, amount, description, category_id, subcategory_id, email_id, source_id, type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (date, amount, description, category_id, subcategory_id, email_id, source_id, type))
            
            transaction_id = self.cursor.lastrowid
            self.conn.commit()
            
            logger.info(
                f"Transaction added [ID: {transaction_id}] | "
                f"{amount:+.2f} | {date} | {description or 'No description'} | "
                f"Category: {category_name or 'None'} | Subcategory: {subcategory_name or 'None'}"
            )
            
            return transaction_id
        except sqlite3.IntegrityError as e:
            if email_id and "UNIQUE constraint failed: transactions.email_id" in str(e):
                logger.warning(f"Skipped duplicate transaction (email_id: {email_id})")
                self.conn.rollback()
                return None  # or raise if you prefer strict mode
            else:
                logger.error(f"Integrity error adding transaction: {e}")
                self.conn.rollback()
                raise    
        except sqlite3.Error as e:
            logger.error(f"Database error adding transaction: {e}")
            self.conn.rollback()
            raise