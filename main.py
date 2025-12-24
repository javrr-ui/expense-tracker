from core.google_auth import get_credentials
from core.gmail_service import get_gmail_service
from core.fetch_emails import get_message, list_messages, parse_email, save_email_body
from constants.banks import SupportedBanks
from database.database import Database
from core.logging_config import setup_logging
from core.parsers.parser_helper import ParserHelper 
from constants.banks import bank_emails
import logging

logger = setup_logging(level=logging.DEBUG)

def build_global_query() -> str:
    bank_queries = [build_query_for_bank(bank) for bank in SupportedBanks]
    return " OR ".join(bank_queries)

def build_query_for_bank(bank: SupportedBanks) -> str:
    """
    Creates a Gmail query like:
    from:(noreply@hey.inc OR alertas@hey.inc OR noreply@heybanco.com OR alertas@heybanco.com)
    """
    senders = bank_emails[bank]
    quoted_senders = [f'"{sender}"' if ' ' in sender else sender for sender in senders]
    or_part = " OR ".join([f"from:{sender}" for sender in quoted_senders])
    return f"({or_part})"

def main():
    logger.info("Starting expense tracking process")
    
    db = Database()
    creds = get_credentials()
    service = get_gmail_service(creds)
    
    query = build_global_query()

    messages = list_messages(service, query=query, max_results=120)
    for msg_meta in messages:
        msg_id = msg_meta['id']
        msg = get_message(service, msg_id)
        email_message = parse_email(msg, msg_id)
        
        save_email_body(email_message, msg_id)
        
        from_header = email_message.get('from', '')
        parser = ParserHelper.get_parser_for_email(from_header)
        
        if parser is None:
            logger.warning(f"No parser found for email from: {from_header}")
            continue
         
        transaction = parser.parse(email_message)
        if transaction:
            db.add_transaction(transaction, msg_id)

    db.close()
    logger.info("Process completed")

if __name__ == '__main__':
    main()