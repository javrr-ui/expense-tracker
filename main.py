from core.google_auth import get_credentials
from database.database import Database
from core.logging_config import setup_logging
import logging
logger = setup_logging(level=logging.INFO)

def main():
    logger.info("Starting expense tracking process")
    db = Database()
    
    creds = get_credentials()
    db.close()

if __name__ == '__main__':
    main()