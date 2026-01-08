import logging
import re
from datetime import datetime

from constants.banks import SupportedBanks
from models.transaction import Transaction

from .base_parser import BaseBankParser

logger = logging.getLogger("expense_tracker")

SPANISH_TO_ENGLISH_MONTH = {
    "ENE": "JAN",
    "FEB": "FEB",
    "MAR": "MAR",
    "ABR": "APR",
    "MAY": "MAY",
    "JUN": "JUN",
    "JUL": "JUL",
    "AGO": "AUG",
    "SEP": "SEP",
    "OCT": "OCT",
    "NOV": "NOV",
    "DIC": "DEC",
}


class NubankParser(BaseBankParser):
    bank_name = SupportedBanks.NUBANK

    CREDIT_CARD_PAYMENT_SUBJECT = "¡Recibimos tu pago!"
    SPEI_OUTGOING_SUBJECT = "Tu transferencia fue exitosa"
    SPEI_RECEPTION_SUBJECT = "¡Recibiste una transferencia!"

    def parse(self, email_message, email_id: str) -> Transaction | None:
        subject = self._decode_subject(email_message.get("subject", ""))
        body = email_message.get("body_plain", "")
        date = email_message.get("date", "")

        if self.CREDIT_CARD_PAYMENT_SUBJECT in subject:
            tx = self._parse_credit_card_payment(body, date, email_id)
            return tx

        if self.SPEI_OUTGOING_SUBJECT in subject:
            tx = self._parse_outgoing_transfer(body, email_id)
            return tx

        if self.SPEI_RECEPTION_SUBJECT in subject:
            tx = self._parse_spei_reception(body, date, email_id)
            return tx

    def _parse_outgoing_transfer(
        self, body_html: str, email_id: str
    ) -> Transaction | None:
        amount = 0.0
        description = "Transferencia"
        datetime_obj = None

        amount_match = re.search(r"Monto\s*:\s*\$?\s*([\d,]+(?:\.\d{2})?)", body_html)
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            amount = float(amount_str)

        date_pattern = r"Fecha\s*:\s*(\d{1,2}/[A-Z]{3}/\d{4})"
        time_pattern = r"Hora\s*:\s*(\d{1,2}:\d{2})"

        date_match = re.search(date_pattern, body_html)
        time_match = re.search(time_pattern, body_html)

        if date_match and time_match:
            date_str = date_match.group(1)
            time_str = time_match.group(1)

            # Combine and parse into datetime object
            datetime_str = f"{date_str} {time_str}"

            datetime_obj = self.parse_nubank_datetime(datetime_str)
            # 2025-12-21 14:03:00

        return Transaction(
            source=self.bank_name,
            email_id=email_id,
            date=datetime_obj,
            amount=amount,
            description=description,
            merchant=None,
            reference=None,
            type="expense",
        )

    def _parse_credit_card_payment(
        self, body_html: str, date: str, email_id: str
    ) -> Transaction | None:
        amount = 0.0
        description: str = "Pago tarjeta de crédito Nu"
        datetime_obj = None

        amount_match = re.search(r"\$([\d,]+\.\d{2})", body_html)
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            amount = float(amount_str)

        datetime_obj = self.parse_email_date(date)
        if datetime_obj is None:
            return None

        return Transaction(
            source=self.bank_name,
            email_id=email_id,
            date=datetime_obj,
            amount=amount,
            description=description,
            merchant=None,
            reference=None,
            type="expense",
        )

    def _parse_spei_reception(
        self, body_html: str, date: str, email_id: str
    ) -> Transaction | None:
        amount = 0.0
        description: str = "Transferencia"
        datetime_obj = None

        amount_match = re.search(r"\$([\d,]+\.\d{2})", body_html)
        if amount_match:
            amount_str = amount_match.group(1).replace(",", "")
            amount = float(amount_str)

        datetime_obj = self.parse_email_date(date)
        if datetime_obj is None:
            return None

        return Transaction(
            source=self.bank_name,
            email_id=email_id,
            date=datetime_obj,
            amount=amount,
            description=description,
            merchant=None,
            reference=None,
            type="income",
        )

    def parse_nubank_datetime(self, datetime_str):
        date_part, time_part = datetime_str.strip().split(" ")

        # Split date: day/month/year
        day, month_es, year = date_part.split("/")

        # Convert Spanish month to English
        month_en = SPANISH_TO_ENGLISH_MONTH.get(month_es.upper())
        if not month_en:
            raise ValueError(f"Unknown month abbreviation: {month_es}")

        # Reconstruct date in English format
        english_date = f"{day}/{month_en}/{year}"

        # Combine back with time
        english_datetime_str = f"{english_date} {time_part}"

        # Now parse safely
        return datetime.strptime(english_datetime_str, "%d/%b/%Y %H:%M")

    def parse_email_date(self, date_str: str) -> datetime | None:
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

        print(f"Failed to parse date: '{date_str}'")
        return None

    def __str__(self):
        return "NubankParser(SPEI transfers & credit card payments)"

    def __repr__(self) -> str:
        return f"NubankParser(bank_name='{self.bank_name}')"
