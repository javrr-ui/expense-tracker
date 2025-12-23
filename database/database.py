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
                    description TEXT,
                    category_id INTEGER,
                    subcategory_id INTEGER,
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