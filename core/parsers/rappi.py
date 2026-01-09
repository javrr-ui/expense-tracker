"""RappiCard email parser.

This module contains the RappiParser, which processes payment confirmation emails
from RappiCard (Rappi Banco) in Mexico.

Currently supports:
- Standard credit card payment confirmations
- Payment confirmations with cashback rewards
"""

import logging
import re
from datetime import datetime

from constants.banks import SupportedBanks
from models.transaction import Transaction

from .base_parser import BaseBankParser

logger = logging.getLogger("expense_tracker")

SPANISH_TO_ENGLISH_MONTH = {
    "ene": "Jan",
    "feb": "Feb",
    "mar": "Mar",
    "abr": "Apr",
    "may": "May",
    "jun": "Jun",
    "jul": "Jul",
    "ago": "Aug",
    "sep": "Sep",
    "oct": "Oct",
    "nov": "Nov",
    "dic": "Dec",
}


class RappiParser(BaseBankParser):
    """Parser for RappiCard (Rappi Banco) payment notification emails.

    Recognizes and extracts details from emails confirming payments made to
    the Rappi credit card, including those that mention cashback rewards.
    """

    bank_name = SupportedBanks.RAPPI

    CREDIT_CARD_PAYMENT_SUBJECT = "Recibimos el pago de tu Rappicard"
    CREDIT_CARD_PAYMENT_WITH_CASHBACK_SUBJECT = "Recibimos el abono de tu Rappicard"

    def parse(self, email_message, email_id: str) -> Transaction | None:
        subject = self._decode_subject(email_message.get("subject", ""))
        body = email_message.get("body_plain", "")

        if not body:
            body = email_message.get("body_plain", "")

        if self.CREDIT_CARD_PAYMENT_SUBJECT in subject:
            tx = self._parse_credit_card_payment(body, email_id)
            return tx

        if self.CREDIT_CARD_PAYMENT_WITH_CASHBACK_SUBJECT in subject:
            tx = self._parse_credit_card_payment(body, email_id)
            return tx

    def _parse_credit_card_payment(
        self, body_html: str, email_id: str
    ) -> Transaction | None:
        """Extract payment amount and date from a RappiCard payment confirmation email.

        The email typically contains:
        - An amount in Mexican pesos (e.g., $1,234.56)
        - A date in Spanish format (e.g., "15 ene 2026")

        Args:
            body_html: Plain text body of the email
            email_id: Gmail message ID

        Returns:
            Transaction representing the credit card payment, or None if parsing fails
        """

        amount = 0.0
        description: str = "Pago de Rappicard"
        datetime_obj = None

        amount_match = re.search(r"\$\s*([\d,]+(?:\.\d{1,2})?)", body_html)
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            amount = float(amount_str)

        date_pattern = r"(\d{1,2} [a-z]{3} \d{4})"

        date_match = re.search(date_pattern, body_html, re.IGNORECASE)
        if date_match:
            date_str = date_match.group(1).lower()
            try:
                for es, en in SPANISH_TO_ENGLISH_MONTH.items():
                    date_str = date_str.replace(es, en)
                datetime_obj = datetime.strptime(date_str, "%d %b %Y")
            except (ValueError, TypeError, OverflowError) as e:
                logger.error("Error parsing date %s: %s", date_str, e)

        return Transaction(
            amount=amount,
            date=datetime_obj,
            email_id=email_id,
            source=self.bank_name,
            description=description,
            merchant=None,
            reference=None,
            type="expense",
        )
