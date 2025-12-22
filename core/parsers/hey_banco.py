import re
import email
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse as date_parser
from .base_parser import BaseBankParser
from models.transaction import Transaction



class HeyBancoParser(BaseBankParser):
    bank_name = "hey_banco"
    
    SPEI_RECEPTION = 'Recepción de transferencia nacional SPEI'
    SPEI_OUTGOING = 'Banca Electrónica Hey, Solicitud de Transferencia Nacional SPEI.'
    
    def parse(self, email_message) -> Transaction | None:
        
        subject = self._decode_subject(email_message.get('subject',''))
        _from = email_message.get('from','')
        body = email_message.get('body_html', '')

        # print(body)
        
        if self.SPEI_RECEPTION in subject:
            tx = self._parse_spei_reception(body)
            return tx

        if self.SPEI_OUTGOING in subject:
            tx = self._parse_outgoing_transfer(body)
            return tx
            
        
    def _parse_spei_reception(self, text) -> Transaction | None:
        amount = 0.0
        description = ""
        datetime_obj = None
        
        amount_match = re.search(r'Cantidad\s*<br\s*/?>\s*<span\b[^>]*>([0-9]+(?:\.[0-9]+)?)</span>', text)
        
        if amount_match:
            amount = amount_match.group(1)
            
        description_match = re.search(r'Concepto\s+pago\s*:\s*<br\s*/?>\s*<span\b[^>]*>([^<]+)</span>', text)
        if description_match:
            description = description_match.group(1)
            

        date_match = re.search(r'Fecha\s+de\s+aplicaci[oó&oacute;]+n\s*:\s*<br\s*/?>\s*<span\b[^>]*>([^<]+)</span>', text)
        if date_match:
            date_str = date_match.group(1)

            try:
                datetime_obj = datetime.strptime(date_str.strip(), "%d %b %Y %H:%M:%S %p")
                
            except ValueError as e:
                print(f"Error parseando fecha: {date_str} -> {e}")
            
        return Transaction(
            bank_name=self.bank_name,
            date=datetime_obj,
            amount=amount,
            description=description,
            type="spei_reception",
            merchant=None,
            reference=None,
            status=""
        )

    def _parse_outgoing_transfer(self, text) -> Transaction | None:
        amount = 0.0
        description = ""
        datetime_obj = None

        amount_match = re.search(r'\$\s*([\d,]+\.?\d*)', text)
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(',', ''))
            except ValueError:
                print(f"Failed to parse amount: {amount_match.group(1)}")
                return None
        
        description_match = re.search(r'Concepto\s+de\s+Pago.*?<\s*span[^>]*>\s*([\s\S]*?)\s*</span>', text, re.IGNORECASE | re.DOTALL)
        if description_match:
            description = description_match.group(1).strip()


        date_match = re.search(r'Fecha\s+de\s+solicita.*?<\s*span[^>]*>\s*(.+?)\s*</span>', text, re.IGNORECASE | re.DOTALL)
        if date_match:
            date_str = date_match.group(1).strip()
            # Normalize Spanish months and AM/PM to English equivalents that dateutil understands
            month_map = {
                'enero': 'January',
                'febrero': 'February',
                'marzo': 'March',
                'abril': 'April',
                'mayo': 'May',
                'junio': 'June',
                'julio': 'July',
                'agosto': 'August',
                'septiembre': 'September',
                'octubre': 'October',
                'noviembre': 'November',
                'diciembre': 'December',
            }

            # Replace Spanish month with English
            normalized_date_str = date_str
            for spanish, english in month_map.items():
                normalized_date_str = normalized_date_str.replace(spanish, english)
                normalized_date_str = normalized_date_str.replace(spanish.capitalize(), english)

            # Normalize "a. m." and "p. m." to "AM" / "PM"
            normalized_date_str = normalized_date_str.replace('a. m.', 'AM').replace('p. m.', 'PM')

            try:
                datetime_obj = date_parser(normalized_date_str, dayfirst=True)
            except Exception as e:
                print(f"Failed to parse date (even after normalization): {date_str} -> {e}")
                datetime_obj = None

        return Transaction(
            bank_name=self.bank_name,
            date=datetime_obj,
            amount=amount,
            description=description,
            type="spei_outgoing",
            merchant=None,
            reference=None,
            status=""
        )