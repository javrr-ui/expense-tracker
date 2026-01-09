"""Main entry point for the Expense Tracker application.

This script orchestrates the entire process of:
- Authenticating with Gmail API
- Searching for bank notification emails
- Parsing emails using bank-specific parsers
- Saving email bodies locally for debugging
- Storing valid transactions in the SQLite database

It runs as a standalone script and is intended to be executed periodically
(e.g., via cron or manual run) to import new transactions.
"""

import logging

from constants.banks import SupportedBanks, bank_emails
from core.fetch_emails import get_message, list_messages, parse_email, save_email_body
from core.gmail_service import get_gmail_service
from core.google_auth import get_credentials
from core.logging_config import setup_logging
from core.parsers.parser_helper import ParserHelper
from database.database import Database

logger = setup_logging(level=logging.DEBUG)


def build_global_query() -> str:
    """
    Build a complete Gmail search query that covers all supported banks.

    Combines individual bank queries with OR operators.

    Returns:
        A string suitable for use with Gmail API's messages.list(q=...)
    """
    bank_queries = [build_query_for_bank(bank) for bank in SupportedBanks]
    return " OR ".join(bank_queries)


def build_query_for_bank(bank: SupportedBanks) -> str:
    """
    Creates a Gmail query like:
    from:(noreply@hey.inc OR alertas@hey.inc OR noreply@heybanco.com OR alertas@heybanco.com)
    """
    senders = bank_emails[bank]
    quoted_senders = [f'"{sender}"' if " " in sender else sender for sender in senders]
    or_part = " OR ".join([f"from:{sender}" for sender in quoted_senders])
    return f"({or_part})"


def main():
    """
    Main execution function of the expense tracker.

    Performs the full workflow:
    1. Sets up logging
    2. Authenticates with Gmail
    3. Searches for emails from supported banks
    4. Parses each email with the appropriate bank parser
    5. Saves transactions to the database

    Handles errors gracefully and ensures the database connection is closed.
    """
    logger.info("Starting expense tracking process")

    db = Database()
    creds = get_credentials()
    service = get_gmail_service(creds)

    query = build_global_query()

    try:
        for msg_meta in list_messages(service, query=query):
            msg_id = msg_meta["id"]

            msg = get_message(service, msg_id)
            email_message = parse_email(msg, msg_id)

            save_email_body(email_message, msg_id)

            from_header = email_message.get("from", "")
            parser = ParserHelper.get_parser_for_email(from_header)

            if parser is None:
                logger.warning("No parser found for email from: %s", from_header)
                logger.warning("message_id: %s", msg_id)
                continue

            transaction = parser.parse(email_message, msg_id)
            if transaction:
                db.add_transaction(transaction)

        logger.info("Process completed")
    except Exception as e:
        logger.error("An error occurred: %s", e, exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
