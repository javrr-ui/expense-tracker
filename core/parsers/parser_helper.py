import logging

from constants.banks import SupportedBanks, bank_emails
from core.parsers.hey_banco import HeyBancoParser
from core.parsers.nubank import NubankParser
from core.parsers.rappi import RappiParser
from core.parsers.banorte import BanorteParser

logger = logging.getLogger("expense_tracker")

PARSERS = {
    SupportedBanks.HEY_BANCO: HeyBancoParser(),
    SupportedBanks.NUBANK: NubankParser(),
    SupportedBanks.RAPPI: RappiParser(),
    # SupportedBanks.PAYPAL: PayPalParser(),
    SupportedBanks.BANORTE: BanorteParser(),
}

class ParserHelper:
    
    @staticmethod
    def get_parser_for_email(from_header: str) -> HeyBancoParser | NubankParser | RappiParser | None:
        """
        Determines which bank/parser to use based on the From: address.
        """
        from_lower = from_header.lower()
        for bank , emails in bank_emails.items():
            if any(email.lower() in from_lower for email in emails):                
                return PARSERS.get(bank)