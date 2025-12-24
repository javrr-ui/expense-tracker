from abc import ABC, abstractmethod
from typing import List
from models.transaction import Transaction
from email.header import decode_header

class BaseBankParser(ABC):
    bank_name = "generic"

    @abstractmethod
    def parse(self, email_message) -> Transaction | None:
        pass
    
    def _decode_subject(self, subject: str) -> str:
        if not subject:
            return ''
        
        return ''.join(
            fragment.decode(encoding or 'utf-8', errors='replace')
            if isinstance(fragment, bytes)
            else fragment
            for fragment, encoding in decode_header(subject)
        )