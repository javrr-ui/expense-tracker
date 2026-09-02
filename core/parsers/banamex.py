"""Banamex (Citibanamex) notification email parser.

Supports:
- Card purchases / ATM ("Retiro/Compra con tarjeta Banamex")
- Incoming SPEI deposits ("Depósito a Cuenta o Tarjeta Banamex")
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from html import unescape

from constants.banks import SupportedBanks
from models.transaction import TransactionCreate
from core.parsers.base_parser import BaseBankParser

logger = logging.getLogger("expense_tracker")

SPANISH_MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}


class BanamexParser(BaseBankParser):
    bank_name = SupportedBanks.BANAMEX

    PURCHASE_SUBJECT = "retiro/compra"
    DEPOSIT_SUBJECT = "depósito a cuenta"

    def parse(self, email_message, email_id: str) -> TransactionCreate | None:
        subject = self._decode_subject(email_message.get("subject", ""))
        body = email_message.get("body_html") or email_message.get("body_plain") or ""
        if not body:
            return None
        text = _flatten(body)
        lowered = subject.lower()
        if "preferencias" in lowered or "modificado tus datos" in text.lower():
            return None
        if self.PURCHASE_SUBJECT in lowered or "retiro / compra" in text.lower():
            return self._parse_purchase(text, email_id)
        if self.DEPOSIT_SUBJECT in lowered or "depósito a cuenta" in text.lower():
            return self._parse_deposit(text, email_id)
        return None

    def _parse_purchase(self, text: str, email_id: str) -> TransactionCreate | None:
        amount = _first_amount(text)
        if amount is None:
            return None
        merchant = _field(text, r"Establecimiento\s+(.+?)\s+Fecha y hora")
        reference = _field(text, r"No\.\s*Autorizaci[oó]n\s+(\d+)")
        when = _parse_datetime(text)
        return TransactionCreate(
            bank_name=self.bank_name,
            email_id=email_id,
            date=when,
            amount=amount,
            description=merchant or "Compra Banamex",
            merchant=merchant,
            reference=reference,
            type="expense",
            kind="purchase",
        )

    def _parse_deposit(self, text: str, email_id: str) -> TransactionCreate | None:
        amount = _first_amount(text)
        if amount is None:
            return None
        medio = _field(text, r"Medio\s+(SPEI\s+\d+)")
        reference = _field(text, r"No\.\s*Autorizaci[oó]n\s+(\d+)")
        when = _parse_datetime(text)
        return TransactionCreate(
            bank_name=self.bank_name,
            email_id=email_id,
            date=when,
            amount=amount,
            description=medio or "Depósito Banamex",
            merchant=None,
            reference=reference or (medio.split()[-1] if medio else None),
            type="income",
            kind="income",
        )


def _flatten(html: str) -> str:
    text = unescape(html)
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def _first_amount(text: str) -> float | None:
    match = re.search(r"Monto\s+\$\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def _field(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    return re.sub(r"\s+", " ", match.group(1)).strip() or None


def _parse_datetime(text: str) -> datetime | None:
    iso = re.search(
        r"Fecha y hora\s+(\d{4}/\d{2}/\d{2})\s+(\d{1,2}:\d{2}:\d{2})\s*(AM|PM)?",
        text,
        re.IGNORECASE,
    )
    if iso:
        date_part, time_part, ampm = iso.group(1), iso.group(2), iso.group(3)
        try:
            if ampm:
                return datetime.strptime(f"{date_part} {time_part} {ampm.upper()}", "%Y/%m/%d %I:%M:%S %p")
            return datetime.strptime(f"{date_part} {time_part}", "%Y/%m/%d %H:%M:%S")
        except ValueError:
            logger.error("Banamex iso datetime parse failed: %s %s %s", date_part, time_part, ampm)

    spanish = re.search(
        r"Fecha y hora\s+(\d{1,2})\s+([A-Za-záéíóú]+)\s+(\d{4})\s*/\s*(\d{1,2}:\d{2}:\d{2})",
        text,
        re.IGNORECASE,
    )
    if spanish:
        day, month_name, year, time_part = spanish.groups()
        month = SPANISH_MONTHS.get(month_name.lower())
        if month:
            try:
                hour, minute, second = (int(part) for part in time_part.split(":"))
                return datetime(int(year), month, int(day), hour, minute, second)
            except ValueError:
                logger.error("Banamex spanish datetime parse failed: %s", spanish.group(0))
    return None
