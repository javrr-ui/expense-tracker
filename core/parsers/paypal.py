"""PayPal email parser.

This module contains the PayPalParser, responsible for extracting transaction
information from PayPal notification emails.

It handles two PayPal email templates:
- Old format: hidden div with GMT timestamp + transaction ID
- New format: preHeader without date, structured table with Fecha / Id. de transaccion

Supported transaction types:
- Payment sent to merchants (expense)
- Authorized payments (expense)
- Bank transfers from PayPal (expense)
- Payment received notifications (income)
"""

import logging
import re
from datetime import datetime
from typing import Literal, Optional

from dateutil.parser import parse as date_parser

from constants.banks import SupportedBanks
from models.transaction import TransactionCreate
from core.parsers.base_parser import BaseBankParser

logger = logging.getLogger("expense_tracker")

BANK_TRANSFER_ES = "transfiriendo"
BANK_TRANSFER = "transfer"


class PayPalParser(BaseBankParser):
    """Parser for PayPal notification emails (Mexico)."""

    bank_name = SupportedBanks.PAYPAL

    def parse(self, email_message, email_id: str) -> Optional[TransactionCreate]:
        """Parse a PayPal email notification."""
        subject = self._decode_subject(email_message.get("subject", ""))
        body = email_message.get("body_html", "")
        if not body:
            body = email_message.get("body_plain", "")

        if not body:
            return None

        subject_lower = subject.lower()

        skip_patterns = [
            "contrase", "bienvenida", "bienvenido", "one touch", "pago peri",
            "confirm", "configur", "eliminado", "asociado", "asoci",
            "cancelado", "active su cuenta", "active tu cuenta",
            "introducci", "acceso", "restaurado", "verificaci",
            "nueva forma de pago", "ha configurado", "le damos",
            "su pago peri", "gracias por abrir", "abrir una cuenta",
            "cambios en la forma", "hemos hecho", "mejorando",
            "hablamos de recompensa", "nueva app", "sorpresa",
            "hablemos de recompensa", "actualice la informaci",
        ]
        if any(p in subject_lower for p in skip_patterns):
            return None

        txn_type = self._determine_type(subject_lower, body)
        date = self._extract_date(body)
        amount, _currency = self._extract_amount(body)

        if amount <= 0:
            return None

        description = subject
        merchant = self._extract_merchant(body, subject)
        reference = self._extract_reference(body)

        return TransactionCreate(
            bank_name=self.bank_name,
            email_id=email_id,
            date=date,
            amount=amount,
            description=description,
            merchant=merchant,
            reference=reference,
            status="",
            type=txn_type,
        )

    @staticmethod
    def _determine_type(
        subject_lower: str, body: str
    ) -> Literal["expense", "income"]:
        """Determine if the transaction is income or expense."""
        body_lower = body.lower()

        income_subject_patterns = [
            "te ha enviado", "te han pagado", "has recibido",
            "you've been paid",
        ]
        for pattern in income_subject_patterns:
            if pattern in subject_lower:
                return "income"

        income_body_patterns = [
            "recibiste un pago",
        ]
        for pattern in income_body_patterns:
            if pattern in body_lower:
                return "income"

        return "expense"

    @staticmethod
    def _extract_date(body: str) -> Optional[datetime]:
        """Extract the transaction date, handling both old and new PayPal templates."""
        month_map = {
            "ene": "Jan", "feb": "Feb", "mar": "Mar", "abr": "Apr",
            "may": "May", "jun": "Jun", "jul": "Jul", "ago": "Aug",
            "sep": "Sep", "oct": "Oct", "nov": "Nov", "dic": "Dec",
            "enero": "January", "febrero": "February", "marzo": "March",
            "abril": "April", "mayo": "May", "junio": "June",
            "julio": "July", "agosto": "August", "septiembre": "September",
            "octubre": "October", "noviembre": "November", "diciembre": "December",
        }

        # New template: "Fecha de la transacción</strong></span><br /><span>1 may 2026</span>"
        # or "7 de marzo de 2026"
        date_match = re.search(
            r'Fecha\s+de\s+la\s+transacci[oó]n'
            r'.*?</strong>\s*</span>\s*<br\s*/?>\s*<span[^>]*>\s*'
            r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4}|\d{1,2}\s+\w+\s+\d{4})'
            r'\s*</span>',
            body,
            re.IGNORECASE,
        )
        if date_match:
            date_str = date_match.group(1).strip()
            # Normalize: replace Spanish month names, strip "de"
            normalized = re.sub(r'\bde\b', '', date_str, flags=re.IGNORECASE)
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            for spanish, english in month_map.items():
                normalized = re.sub(
                    rf'\b{spanish}\b', english, normalized, flags=re.IGNORECASE
                )
            try:
                return date_parser(normalized, dayfirst=True)
            except (ValueError, TypeError, OverflowError) as e:
                logger.error("Failed to parse PayPal date (new): %s -> %s", date_str, e)

        # Old template: hidden div with GMT timestamp
        date_match = re.search(
            r'(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2})\s+GMT',
            body,
        )
        if not date_match:
            date_match = re.search(
                r'display:inline;">(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2})\s+GMT',
                body,
            )

        if date_match:
            date_str = date_match.group(1).strip()
            try:
                return datetime.strptime(date_str, "%d/%m/%Y %H:%M:%S")
            except ValueError as e:
                logger.error("Failed to parse PayPal date (old): %s -> %s", date_str, e)

        return None

    @staticmethod
    def _extract_amount(body: str) -> tuple[float, str]:
        """Extract the transaction amount and currency."""
        # New template: "Ha pagado $6.00 USD a Merchant" or "Usted envió $5.60 USD a X"
        for prefix in [r'Ha\s+pagado', r'Usted\s+envi[oó]']:
            match = re.search(
                rf'{prefix}\s+\$([\d,]+\.\d{2})\s*&nbsp;?\s*(MXN|USD|EUR)',
                body,
                re.IGNORECASE,
            )
            if match:
                try:
                    amount = float(match.group(1).replace(",", ""))
                    return amount, match.group(2).upper()
                except ValueError:
                    pass

        patterns = [
            r'importe\s+de\s+\$([\d,]+\.\d{2})\s+(MXN|USD|EUR)',
            r'por\s+importe\s+de\s+\$([\d,]+\.\d{2})\s+(MXN|USD|EUR)',
            r'transfiriéramos\s+\$([\d,]+\.\d{2})\s+(MXN|USD|EUR)',
            r'transferido\s+\$([\d,]+\.\d{2})\s+(MXN|USD|EUR)',
            r'Importe\s+total\s+transferido[^<]*?\$([\d,]+\.\d{2})\s+(MXN|USD|EUR)',
            r'\$([\d,]+\.\d{2})\s+(MXN|USD|EUR)',
        ]

        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(",", ""))
                    currency = match.group(2).upper()
                    return amount, currency
                except ValueError:
                    continue

        return 0.0, "MXN"

    @staticmethod
    def _extract_merchant(body: str, subject: str) -> Optional[str]:
        """Extract the merchant name from new or old template."""
        # New template: "Comercio</strong></span><br /><span>Vultr"
        merchant_match = re.search(
            r'Comercio\s*</strong>\s*</span>\s*<br\s*/?>\s*<span[^>]*>\s*'
            r'([^<\n]+?)\s*(?:<br|</span)',
            body,
            re.IGNORECASE | re.DOTALL,
        )
        if merchant_match:
            merchant = merchant_match.group(1).strip()
            if merchant:
                return merchant

        # Old template: "Comercio</span><br/><span...>NAME</span>"
        merchant_match = re.search(
            r'Comercio\s*</span><br/>\s*<span[^>]*>([^<]+)',
            body,
            re.IGNORECASE | re.DOTALL,
        )
        if merchant_match:
            return merchant_match.group(1).strip()

        # From new template headline: "Ha pagado $X.XX USD a Vultr" or "Usted envió $X.XX USD a X"
        for prefix in [r'Ha\s+pagado', r'Usted\s+envi[oó]']:
            headline_match = re.search(
                rf'{prefix}\s+\$[\d,]+\.\d{{2}}\s*&nbsp;?\s*\w+\s+a\s+([^<]+)',
                body,
                re.IGNORECASE,
            )
            if headline_match:
                merchant = headline_match.group(1).strip()
                if merchant:
                    return merchant

        # From subject: "Ha autorizado un pago a X"
        dest_match = re.search(
            r'(?:Ha autorizado un pago a|Se ha procesado su pago a)\s+(.+?)(?:\s*<|$)',
            subject,
            re.IGNORECASE,
        )
        if dest_match:
            return dest_match.group(1).strip().rstrip(".")

        return None

    @staticmethod
    def _extract_reference(body: str) -> Optional[str]:
        """Extract the PayPal transaction ID (old and new templates)."""
        # New template: "Id. de transacción</strong></span><br /><a...><span>REF</span></a>"
        ref_match = re.search(
            r'Id\.\s+de\s+transacci[oó]n\s*</strong>'
            r'.*?<span[^>]*>\s*(\w{10,})\s*</span>',
            body,
            re.IGNORECASE | re.DOTALL,
        )
        if ref_match:
            return ref_match.group(1).strip()

        # Old template: "Id. de transacción: REF"
        ref_match = re.search(
            r'Id\.\s+de\s+transacción:\s*(?:<[^>]+>)*\s*([\w]+)',
            body,
        )
        if ref_match:
            return ref_match.group(1).strip()

        # Old template bank transfer: "Número de transacción</th><td>REF"
        ref_match = re.search(
            r'Número\s+de\s+transacción[^<]*</th>\s*<td[^>]*>(?:<[^>]+>)*\s*([\w]+)',
            body,
        )
        if ref_match:
            return ref_match.group(1).strip()

        return None

    def __str__(self) -> str:
        return "PayPalParser(payments, receipts, bank transfers)"

    def __repr__(self) -> str:
        return f"PayPalParser(bank_name='{self.bank_name}')"
