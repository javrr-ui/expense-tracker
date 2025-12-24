import re
import email
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil.parser import parse as date_parser
from .base_parser import BaseBankParser
from models.transaction import Transaction
from constants.banks import SupportedBanks
from unidecode import unidecode
import logging 

logger = logging.getLogger("expense_tracker")

class HeyBancoParser(BaseBankParser):
    bank_name = SupportedBanks.HEY_BANCO
    
    SPEI_RECEPTION = 'Recepción de transferencia nacional SPEI'
    SPEI_OUTGOING = 'Banca Electrónica Hey, Solicitud de Transferencia Nacional SPEI.'
    CREDIT_CARD_PAYMENT = 'Banca Electrónica Hey, Solicitud de pago de Tarjeta Hey'
    CREDIT_CARD_PURCHASE = 'Servicio de Alertas HeyBanco'
    
    def parse(self, email_message) -> Transaction | None:
        
        subject = self._decode_subject(email_message.get('subject',''))
        body = email_message.get('body_html', '')

        if not body:
            body = email_message.get('body_plain', '')
        
        if self.SPEI_RECEPTION in subject:
            tx = self._parse_spei_reception(body)
            return tx

        if self.SPEI_OUTGOING in subject:
            tx = self._parse_outgoing_transfer(body)
            return tx
        
        if self.CREDIT_CARD_PAYMENT in subject:
            tx = self._parse_credit_card_payment(body)
            return tx
        
        if self.CREDIT_CARD_PURCHASE in subject:
            tx = self._parse_credit_card_purchase(body)
            return tx
        
    def _parse_spei_reception(self, text) -> Transaction | None:
        amount = 0.0
        description = ""
        datetime_obj = None
        
        amount_match = re.search(r'Cantidad\s*<br\s*/?>\s*<span\b[^>]*>([0-9]+(?:\.[0-9]+)?)</span>', text)
        
        if amount_match:
            amount = amount = float(amount_match.group(1).replace(',', ''))
            
        description_match = re.search(r'Concepto\s+pago\s*:\s*<br\s*/?>\s*<span\b[^>]*>([^<]+)</span>', text)
        if description_match:
            description = description_match.group(1)
            

        date_match = re.search(r'Fecha\s+de\s+aplicaci[oó&oacute;]+n\s*:\s*<br\s*/?>\s*<span\b[^>]*>([^<]+)</span>', text)
        if date_match:
            date_str = date_match.group(1)

            try:
                datetime_obj = datetime.strptime(date_str.strip(), "%d %b %Y %H:%M:%S %p")
                
            except ValueError as e:
                logger.error(f"Failed to parse date: {date_str} -> {e}")
            
        return Transaction(
            source=self.bank_name,
            date=datetime_obj,
            amount=amount,
            description=description,
            merchant=None,
            reference=None,
            status="",
            type="income"
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
                logger.error(f"Failed to parse amount: {amount_match.group(1)}")
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
                logger.error(f"Failed to parse date (even after normalization): {date_str} -> {e}")
                datetime_obj = None

        return Transaction(
            source=self.bank_name,
            date=datetime_obj,
            amount=amount,
            description=description,
            merchant=None,
            reference=None,
            status="",
            type="expense"
        )
    def _parse_credit_card_payment(self, text) -> Transaction | None:
        amount = 0.0
        description = ""
        datetime_obj = None

        amount_match = re.search(r'Monto:[\s\S]*?\$\s*<span>([\d,]+\.\d{2})</span>', text, re.IGNORECASE | re.DOTALL)
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(',', ''))
            except ValueError:
                logger.error(f"Failed to parse amount: {amount_match.group(1)}")
                return None

        description_match = re.search(r'Descripci&oacute;n:[\s\S]*?<span>([^<]+)</span>', text, re.IGNORECASE | re.DOTALL)
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
                logger.error(f"Failed to parse date (even after normalization): {date_str} -> {e}")
                datetime_obj = None
                
        return Transaction(
            source=self.bank_name,
            date=datetime_obj,
            amount=amount,
            description=description,
            merchant=None,
            reference=None,
            status="",
            type="expense"
        )
    def _parse_credit_card_purchase(self, text) -> Transaction | None:
        amount = 0.0
        description = ""
        datetime_obj = None
        transaction_type = ""
        
        if self.is_transaction_not_valid_or_email_not_supported(text):
            return None
        
        amount_match = re.search(r'Cantidad:[\s\S]*?<h4[^>]*>\s*\$?([\d,]+\.\d{2})\s*</h4>', text)
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(',', ''))
            except ValueError:
                logger.error(f"Failed to parse amount: {amount_match.group(1)}")
                return None
        
        description_match = re.search(r'Comercio:[\s\S]*?<h4[^>]*>\s*([^<]+?)\s*</h4>', text)
        if description_match:
            description = description_match.group(1).strip()
            
        date_match = re.search(r'Fecha y hora de la transacci&oacute;n:[\s\S]*?<h4[^>]*>\s*(\d{1,2}/\d{1,2}/\d{4}\s*-\s*\d{2}:\d{2}\s*hrs)\s*</h4>', text)
        if date_match:
            date_str = date_match.group(1)
            cleaned = date_str.replace('hrs', '').strip()
            try:
                datetime_obj =  date_parser(cleaned, dayfirst=True)
            except Exception as e:
                logger.error(f"Failed to parse date: {date_str} -> {e}")
                
        card_type_match = re.search(r'con tu <b>(Credito|Debito|Crédito|Débito|Cr&eacute;dito|D&eacute;bito)</b>', text)
        if card_type_match:
            card = unidecode(card_type_match.group(1).strip().lower())
            
            if card == 'debito':
                transaction_type = "debit_card_purchase"
            if card == 'credito':
                transaction_type = "credit_card_purchase"
        
        return Transaction(
            source=self.bank_name,
            date=datetime_obj,
            amount=amount,
            description=description,
            merchant=None,
            reference=None,
            status="",
            type="expense"
        )
        
    def is_transaction_not_valid_or_email_not_supported(self, text: str) -> bool:
        rejected_match = re.search(r'La compra que realizaste fue rechazada por Fondos Insuficientes', text)
        if rejected_match:
            return True

        freezed_debit_card_match = re.search(r'¡Has bloqueado tu tarjeta de débito', text)
        if freezed_debit_card_match:
            return True
        
        credit_card_payment_failed_match = re.search(r'El pago que intentaste hacer hace un momento no ha sido procesado.', text)
        if credit_card_payment_failed_match:
            return True
        
        user_recover_match = re.search(r'Recuperación de usuario.',text)
        if user_recover_match:
            return True
        
        national_transfer_failed_match = re.search(r'No se ha podido realizar tu transferencia nacional.', text)
        if national_transfer_failed_match:
            return True
        
        invalid_cvv_match = re.search(r'La compra que realizaste fue rechazada por CVV Inválido', text)
        if invalid_cvv_match:
            return True
        
        virtual_card_expired_match = re.search(r'Tu tarjeta virtual tiene nueva fecha de vencimiento', text)
        if virtual_card_expired_match:
            return True
        
        renewal_notice_match = re.search(r'Tu fecha de vencimiento se renovará', text)
        if renewal_notice_match:
            return True

        return False
    
    def __str__(self) -> str:
        return "HeyBancoParser(SPEI transfers, card payments & purchases)"
    
    def __repr__(self) -> str:
        return f"HeyBancoParser(bank_name='{self.bank_name}')"