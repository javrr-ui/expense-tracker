from .base_parser import BaseBankParser
from models.transaction import Transaction
from constants.banks import SupportedBanks
import logging
import re
from datetime import datetime

logger = logging.getLogger("expense_tracker")

SPANISH_TO_ENGLISH_MONTH = {
    "ENE": "JAN", "FEB": "FEB", "MAR": "MAR", "ABR": "APR",
    "MAY": "MAY", "JUN": "JUN", "JUL": "JUL", "AGO": "AUG",
    "SEP": "SEP", "OCT": "OCT", "NOV": "NOV", "DIC": "DEC",
}

class NubankParser(BaseBankParser):
    bank_name = SupportedBanks.NUBANK
    
    CREDIT_CARD_PAYMENT_SUBJECT = "¡Recibimos tu pago!"
    SPEI_OUTGOING_SUBJECT = "Tu transferencia fue exitosa"
    SPEI_RECEPTION_SUBJECT = "¡Recibiste una transferencia!"
    def parse(self, email_message) -> Transaction | None:
        subject = self._decode_subject(email_message.get('subject',''))
        body = email_message.get('body_plain', '')

        
        if self.CREDIT_CARD_PAYMENT_SUBJECT in subject:
            tx = self._parse_credit_card_payment(body)
            return tx

        if self.SPEI_OUTGOING_SUBJECT in subject:
            tx = self._parse_outgoing_transfer(body)
            return tx
        
        if self.SPEI_RECEPTION_SUBJECT in subject:
            tx = self._parse_spei_reception(body)
            return tx
        
    def _parse_outgoing_transfer(self, body_html: str) -> Transaction | None:
        amount = 0.0
        description = "Transferencia"
        datetime_obj = None
        
        amount_match = re.search(r'Monto\s*:\s*\$?\s*([\d,]+(?:\.\d{2})?)', body_html)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
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
            date=datetime_obj,
            amount=amount,
            description=description,
            merchant=None,
            reference=None,
            type="expense"
        )
    
    def _parse_credit_card_payment(self, body_html: str) -> Transaction | None:
        return None
    
    def _parse_spei_reception(self, body_html: str) -> Transaction | None:
        return None
        
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

    def __str__(self):
        return "NubankParser(SPEI transfers & credit card payments)"
    
    def __repr__(self) -> str:
        return f"NubankParser(bank_name='{self.bank_name}')"