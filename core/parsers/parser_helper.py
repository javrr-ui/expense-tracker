"""Parser selection utilities.

This module provides a helper class to route incoming emails to the appropriate
bank-specific parser based on the sender email address.

It maintains a mapping of supported banks to their parser instances and uses
the configured sender email lists to determine the correct parser.
"""

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
    """Utility class for selecting the correct bank parser based on email sender."""

    @staticmethod
    def get_parser_for_email(
        from_header: str,
    ) -> HeyBancoParser | NubankParser | RappiParser | BanorteParser | None:
        """
        Determine the appropriate parser instance based on the email's From header.

        The matching is case-insensitive and checks if any of the known sender
        email addresses for a bank appear in the From header.

        Args:
            from_header: The raw From: header value from the email

        Returns:
            An instantiated parser for the matching bank, or None if no match is found
        """
        from_lower = from_header.lower()
        for bank, emails in bank_emails.items():
            if any(email.lower() in from_lower for email in emails):
                return PARSERS.get(bank)

        return None
