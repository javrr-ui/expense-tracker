from abc import ABC, abstractmethod
from typing import List
from models.transaction import Transaction
import email.header
class BaseBankParser(ABC):
    bank_name = "generic"

    @abstractmethod
    def parse(self, email_message) -> List[Transaction] | None:
        pass
    
    def _decode_subject(self, subject: str) -> str:
        decoded = email.header.decode_header(subject)[0][0]
        if isinstance(decoded, bytes):
            return decoded.decode('utf-8', errors='replace')
        return decoded