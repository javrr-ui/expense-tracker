from core.google_auth import get_credentials
from core.logging_config import setup_logging
import logging
logger = setup_logging(level=logging.INFO)

def main():
    logger.info("Starting expense tracking process")
    
    creds = get_credentials()

if __name__ == '__main__':
    main()