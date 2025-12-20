import re
import email
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
from .base_parser import BaseBankParser
from models.transaction import Transaction



class HeyBancoParser(BaseBankParser):
    bank_name = "hey_banco"
    
    SPEI_RECEPTION = 'Recepción de transferencia nacional SPEI'
    
    def parse(self, email_message) -> Transaction | None:
        
        subject = self._decode_subject(email_message.get('subject',''))
        _from = email_message.get('from','')
        body = email_message.get('body_html', '')

        # print(body)
        
        if self.SPEI_RECEPTION in subject:
            tx = self._parse_spei_reception(body)
            return tx
            
        
    def _parse_spei_reception(self, text) -> Transaction | None:
        amount = 0.0
        description = ""
        datetime_obj = None
        
        amount_match = re.search(r'Cantidad\s*<br\s*/?>\s*<span\b[^>]*>([0-9]+(?:\.[0-9]+)?)</span>', text)
        
        if amount_match:
            amount = amount_match.group(1)
            print(amount)
            
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
            date=datetime_obj,
            amount=amount,
            description=description,
            type="spei_reception",
            merchant=None,
            reference=None,
            status=""
        )