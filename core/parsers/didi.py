"""DiDi (Mexico) email parser.

Handles DiDi Préstamos transactional mail. Marketing, reminders and statement
alerts are ignored.

Supported:
- Loan payment received ("Pago recibido") → expense
- Loan disbursement ("Se depositó el préstamo") → skipped unless a principal
  amount appears in the body (DiDi usually omits it)
"""

from __future__ import annotations

import logging
import re
from datetime import datetime

from dateutil.parser import parse as date_parser

from constants.banks import SupportedBanks
from core.parsers.base_parser import BaseBankParser
from models.transaction import TransactionCreate

logger = logging.getLogger("expense_tracker")

SKIP_SUBJECTS = (
    "recuerda",
    "recordatorio",
    "vencid",
    "venci",
    "estado de cuenta",
    "difiere",
    "refiere",
    "newsletter",
    "invitaci",
    "reembolso",
    "contrato",
    "travel",
    "gasolina",
    "descuento",
    "promo",
    "referido",
    "concierto",
    "maleta",
)


class DidiParser(BaseBankParser):
    """Parser for DiDi Préstamos and DiDi Card notification emails."""

    bank_name = SupportedBanks.DIDI

    def parse(self, email_message, email_id: str) -> TransactionCreate | None:
        subject = self._decode_subject(email_message.get("subject", ""))
        body = email_message.get("body_plain") or email_message.get("body_html") or ""
        if not body:
            return None

        subject_lower = subject.lower()
        if any(token in subject_lower for token in SKIP_SUBJECTS):
            logger.debug("Skipping DiDi non-transactional email: %s", subject)
            return None

        if "pago recibido" in subject_lower:
            return self._parse_payment(body, email_message.get("date", ""), email_id)

        if "se deposit" in subject_lower or "depositó el préstamo" in body.lower() or "deposito el prestamo" in body.lower():
            return self._parse_deposit(body, email_message.get("date", ""), email_id)

        return None

    def _parse_payment(self, body: str, date_header: str, email_id: str) -> TransactionCreate | None:
        amount = self._extract_amount(body)
        if amount <= 0:
            logger.warning("DiDi payment email without amount: %s", email_id)
            return None

        next_due = self._extract_next_due(body)
        description = "Pago DiDi Préstamos"
        if next_due:
            description = f"{description} · siguiente: {next_due}"

        return TransactionCreate(
            bank_name=self.bank_name,
            email_id=email_id,
            date=self._parse_email_date(date_header),
            amount=amount,
            description=description,
            merchant="DiDi Préstamos",
            reference=next_due,
            type="expense",
        )

    def _parse_deposit(self, body: str, date_header: str, email_id: str) -> TransactionCreate | None:
        """Loan disbursement. Principal is usually missing; skip if so."""
        principal = self._extract_principal(body)
        if principal is None:
            logger.info(
                "DiDi loan disbursement has no principal amount, skipping tx: %s",
                email_id,
            )
            return None

        return TransactionCreate(
            bank_name=self.bank_name,
            email_id=email_id,
            date=self._parse_email_date(date_header),
            amount=principal,
            description="Depósito de préstamo DiDi",
            merchant="DiDi Préstamos",
            reference=self._extract_next_due(body),
            type="income",
        )

    @staticmethod
    def _extract_amount(body: str) -> float:
        match = re.search(
            r"pago de\s*MXN\s*\$?\s*([\d,]+(?:\.\d{1,2})?)",
            body,
            re.IGNORECASE,
        )
        if not match:
            match = re.search(r"MXN\s*\$?\s*([\d,]+(?:\.\d{1,2})?)", body, re.IGNORECASE)
        if not match:
            return 0.0
        return float(match.group(1).replace(",", ""))

    @staticmethod
    def _extract_principal(body: str) -> float | None:
        """Only accept an explicit loan principal, not the installment amounts."""
        match = re.search(
            r"(?:monto(?:\s+del)?\s+pr[eé]stamo|pr[eé]stamo de)\s*"
            r"(?:es\s+de\s+)?MXN\s*\$?\s*([\d,]+(?:\.\d{1,2})?)",
            body,
            re.IGNORECASE,
        )
        if match:
            return float(match.group(1).replace(",", ""))
        return None

    @staticmethod
    def _extract_next_due(body: str) -> str | None:
        match = re.search(
            r"vence el\s+(\d{4}-\d{2}-\d{2})",
            body,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
        match = re.search(
            r"vence el\s+(\d{1,2}/\d{1,2}/\d{4})",
            body,
            re.IGNORECASE,
        )
        if match:
            day, month, year = match.group(1).split("/")
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        return None

    @staticmethod
    def _parse_email_date(date_str: str) -> datetime | None:
        if not date_str:
            return None
        try:
            parsed = date_parser(date_str)
            if parsed.tzinfo is not None:
                parsed = parsed.replace(tzinfo=None)
            return parsed
        except (ValueError, TypeError, OverflowError) as exc:
            logger.error("Failed to parse DiDi date %s: %s", date_str, exc)
            return None

    def __str__(self) -> str:
        return "DidiParser(loan payments)"
