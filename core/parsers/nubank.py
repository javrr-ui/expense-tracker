from .base_parser import BaseBankParser
from models.transaction import Transaction

class NubankParser(BaseBankParser):
    bank_name = "nubank"
    
    CREDIT_CARD_PAYMENT_SUBJECT = "¡Recibimos tu pago!"
    SPEI_OUTGOING_SUBJECT = "Tu transferencia fue exitosa"
    SPEI_RECEPTION_SUBJECT = "¡Recibiste una transferencia!"
    def parse(self, email_message) -> Transaction | None:
        subject = self._decode_subject(email_message.get('subject',''))
        body = email_message.get('body_html', '')

        
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
        return None
    
    def _parse_credit_card_payment(self, body_html: str) -> Transaction | None:
        return None
    
    def _parse_spei_reception(self, body_html: str) -> Transaction | None:
        return None
        