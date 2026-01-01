import logging
import re
from datetime import datetime

from dateutil.parser import parse as date_parser
from unidecode import unidecode

from constants.banks import SupportedBanks
from models.transaction import Transaction

from .base_parser import BaseBankParser

logger = logging.getLogger("expense_tracker")

class RappiParser(BaseBankParser):
    bank_name = SupportedBanks.RAPPI
    
    CREDIT_CARD_PAYMENT_SUBJECT = "Recibimos el pago de tu Rappicard"
    
    def parse(self, email_message, email_id: str) -> Transaction | None:
        subject = self._decode_subject(email_message.get('subject',''))
        body = email_message.get('body_plain', '')
        date = email_message.get('date', '')
        
        if self.CREDIT_CARD_PAYMENT_SUBJECT in subject:
            tx = self._parse_credit_card_payment(body, email_id)
            return tx
    
    
    def _parse_credit_card_payment(self, body_html: str, email_id: str) -> Transaction | None:
        amount = 0.0
        description: str = "Pago de Rappicard"
        datetime_obj = None
        
        return None