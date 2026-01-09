"""
Banorte Bank Email Parser Module

This module provides a parser for processing email notifications from Banorte bank (Mexico).
Currently supports parsing of outgoing SPEI transfers.

The parser extracts the following key information from email bodies:
- Transaction amount
- Operation description
- Date and time of the transaction
- Transaction type (currently only expense/outgoing transfers)

It converts Spanish month abbreviations to English for reliable datetime parsing
and creates Transaction model instances compatible with the expense tracking system.

Supported email subjects include:
- "Transferencia a Otros Bancos Nacionales - SPEI"

Usage:
    parser = BanorteParser()
    transaction = parser.parse(email_message_dict, email_id)
"""

import logging
import re
from datetime import datetime


from constants.banks import SupportedBanks
from models.transaction import Transaction

from core.parsers.base_parser import BaseBankParser

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


class BanorteParser(BaseBankParser):
    """
    Parser for Banorte bank emails.

    This class handles parsing of specific Banorte email formats,
    currently supporting outgoing SPEI transfers.
    """

    bank_name = SupportedBanks.BANORTE

    SPEI_OUTGOING = "Transferencia a Otros Bancos Nacionales - SPEI"

    def parse(self, email_message, email_id: str) -> Transaction | None:
        """
        Parse the email message to extract a transaction if it matches supported types.

        Checks the email subject and body to determine the transaction type
        and delegates to the appropriate parsing method.

        Args:
            email_message: Dictionary containing email parts like subject, body_html, body_plain.
            email_id: Unique identifier for the email.

        Returns:
            Transaction object if successfully parsed, otherwise None.
        """

        subject = self._decode_subject(email_message.get("subject", ""))
        body = email_message.get("body_html", "")

        if not body:
            body = email_message.get("body_plain", "")

        if self.SPEI_OUTGOING in subject:
            tx = self._parse_outgoing_transfer(body, email_id)
            return tx

    def _parse_outgoing_transfer(self, text, email_id) -> Transaction | None:
        """
        Parse an outgoing SPEI transfer from the email body.

        Uses regular expressions to extract amount, description, time, and date
        from the HTML-formatted email body.

        Args:
            text: The email body content (HTML or plain text)
            email_id: Unique identifier for the email

        Returns:
            Transaction object if all required fields are parsed successfully,
            otherwise None.
        """
        amount = 0.0
        description = ""
        time = "00:00:00"
        datetime_obj = None

        amount_match = re.search(
            r"Importe: </td>\s*<td nowrap=\"nowrap\">\s*\$([\d,]+\.\d{2}) MN\s*</td>",
            text,
        )

        if amount_match:
            amount = amount = float(amount_match.group(1).replace(",", ""))

        description_match = re.search(
            r"Operación: </td>\s*<td align=\"left\" nowrap=\"nowrap\">\s*(.*?)\s*</td>",
            text,
        )
        if description_match:
            description = description_match.group(1)

        time_match = re.search(
            r'Hora de Operación: </td>\s*<td nowrap="nowrap">\s*(\d{2}:\d{2}:\d{2} horas)\s*</td>',
            text,
            re.DOTALL | re.IGNORECASE,
        )
        if time_match:
            time = time_match.group(1).replace("horas", "").strip()

        date_match = re.search(
            r"Fecha de Operación: </td>\s*<td nowrap=\"nowrap\">\s*"
            r"(\d{1,2}/[A-Za-z]{3}/\d{4})"
            r"\s*</td>",
            text,
        )
        if date_match:
            date_str = date_match.group(1).lower()

            try:
                day, month_es, year = date_str.split("/")
                month_en = SPANISH_TO_ENGLISH_MONTH.get(month_es)

                full_datetime_str = f"{day} {month_en} {year} {time}"
                datetime_obj = datetime.strptime(full_datetime_str, "%d %b %Y %H:%M:%S")
            except (ValueError, TypeError, OverflowError) as e:
                logger.error("Error parsing date '%s': %s", date_str, e)

        return Transaction(
            source=self.bank_name,
            email_id=email_id,
            date=datetime_obj,
            amount=amount,
            description=description,
            merchant=None,
            reference=None,
            status="",
            type="expense",
        )
