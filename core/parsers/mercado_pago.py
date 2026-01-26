"""Mercado Pago parser module."""

import logging
import re
from datetime import datetime

from core.parsers.base_parser import BaseBankParser
from models.transaction import TransactionCreate
from constants.banks import SupportedBanks


logger = logging.getLogger("expense_tracker")


class MercadoPagoParser(BaseBankParser):
    """Parser for Mercado Pago payment notification emails."""

    bank_name = SupportedBanks.MERCADO_PAGO

    SPEI_OUTGOING = "Tu transferencia fue enviada"

    def parse(self, email_message, email_id: str) -> TransactionCreate | None:
        """Parse a Mercado Pago email and return a Transaction if a supported type is found."""

        subject = self._decode_subject(email_message.get("subject", ""))
        body = email_message.get("body_plain", "")
        date = email_message.get("date", "")

        if not body:
            body = email_message.get("body_html", "")

        if self.SPEI_OUTGOING in subject:
            tx = self._parse_outgoing_transfer(body, date, email_id)
            return tx

        return None

    def _parse_outgoing_transfer(
        self, body_html: str, date: str, email_id: str
    ) -> TransactionCreate | None:
        """Parse an outgoing transfer notification from Mercado Pago email body."""
        amount = 0.0
        description = "Transferencia"
        datetime_obj = None

        amount_match = re.search(
            r"transferencia de\s*(?:<span[^>]*>)?\$\s*([\d,]+(?:\.\d{1,2})?)(?:</span>)?\.?",
            body_html,
            re.IGNORECASE | re.DOTALL,
        )
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            amount = float(amount_str)

        datetime_obj = self.parse_email_date(date)
        if datetime_obj is None:
            return None

        return TransactionCreate(
            bank_name=self.bank_name,
            email_id=email_id,
            date=datetime_obj,
            amount=amount,
            description=description,
            merchant=None,
            reference=None,
            type="expense",
        )

    def parse_email_date(self, date_str: str) -> datetime | None:
        """Parse the email Date header into a timezone-naive datetime object.

        Handles common Gmail Date header formats.

        Args:
            date_str: Raw Date header string from the email

        Returns:
            Parsed datetime (timezone-naive) or None if parsing fails
        """
        date_str = date_str.strip()

        # List of possible format
        formats = [
            "%a, %d %b %Y %H:%M:%S %z (%Z)",  # With (UTC)
            "%a, %d %b %Y %H:%M:%S %z",  # With +0000 but no (UTC)
            "%a, %d %b %Y %H:%M:%S",  # Naive (no timezone) - fallback
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
            except ValueError:
                continue

        logger.error("Failed to parse date: %s", date_str)
        return None
