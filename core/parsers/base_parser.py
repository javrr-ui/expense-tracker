from abc import ABC, abstractmethod
from email.header import decode_header
from typing import List

from models.transaction import Transaction


class BaseBankParser(ABC):
    bank_name = "generic"

    @abstractmethod
    def parse(self, email_message, email_id: str) -> Transaction | None:
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