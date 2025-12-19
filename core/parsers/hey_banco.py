import re
import email
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
from .base_parser import BaseBankParser
from models.transaction import Transaction

class HeyBancoParser(BaseBankParser):
    bank_name = "hey_banco"
    
    def parse(self, email_message) -> list[Transaction] | None:
        subject = self._decode_subject(email_message.get('subject',''))
        _from = email_message.get('from','')
        print(subject)
        print(_from)
        