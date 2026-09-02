"""Nu Mexico statement text parser.

Handles:
- Cuenta Nu (checking): "31 JUL 2026 ... -$315.00"
- Tarjeta de crédito (legacy): "05/08/2026 OXXO $120.00"
"""

from __future__ import annotations

import re
from datetime import date, datetime

from core.parsers.statements.base import StatementLine, StatementParseResult

AMOUNT = r"\$?\s*([\d,]+\.\d{2})"
SIGNED_AMOUNT = r"([+-])\s*\$\s*([\d,]+\.\d{2})"
MONTHS = {
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
MONTH_TOKEN = r"(ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)"
CHECKING_LINE = re.compile(
    rf"^(\d{{1,2}})\s+{MONTH_TOKEN}\s+(\d{{4}})(?:\s+(.*?))?\s+{SIGNED_AMOUNT}$",
    re.IGNORECASE,
)
CARD_LINE = re.compile(
    rf"^(\d{{1,2}})\s+{MONTH_TOKEN}\s+(\d{{4}})\s+(\d{{1,2}})\s+{MONTH_TOKEN}\s+(\d{{4}})\s+(.+?)\s+{SIGNED_AMOUNT}$",
    re.IGNORECASE,
)
WEEKDAYS = r"(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)"
SKIP_PREFIXES = (
    "transferencia spei",
    "deposito spei",
    "depósito spei",
    "comision ",
    "comisión ",
    "comisiones cobradas",
    "nubank, s.a",
    "cuenta nu:",
    "rfc:",
    "clabe:",
    "fecha del ",
    "detalle de movimientos",
    "grafico transaccional",
    "gráfico transaccional",
    "como esta organizado",
    "cómo está organizado",
    "contacto",
    "comprobante fiscal",
    "sello digital",
    "cadena original",
    "folio fiscal",
    "dinero generado",
    "ganancia anual",
    "unicamente estan",
    "únicamente están",
    "no cobramos",
    "este es tu estado",
    "si solo tienes",
    "hola,",
    "saldo inicial",
    "saldo final",
    "saldo al ",
    "depositos",
    "depósitos",
    "gastos",
    "periodo:",
)


def _money(value: str) -> float:
    return float(value.replace(",", ""))


def _date(value: str) -> datetime | None:
    value = value.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _spanish_date(day: str, month_token: str, year: str) -> date | None:
    month = MONTHS.get(month_token.lower()[:3])
    if month is None:
        return None
    try:
        return date(int(year), month, int(day))
    except ValueError:
        return None


def parse_nu_statement_text(text: str) -> StatementParseResult:
    result = StatementParseResult(raw_text=text)
    card = _is_credit_card_statement(text)
    _parse_header(result, text, card=card)
    if card:
        result.lines = _parse_credit_card_lines(text)
    elif re.search(rf"\d{{1,2}}\s+{MONTH_TOKEN}\s+\d{{4}}", text, re.IGNORECASE):
        result.lines = _parse_checking_lines(text)
    else:
        result.lines = _parse_legacy_card_lines(text)
    return result


def _is_credit_card_statement(text: str) -> bool:
    blob = text.lower()
    return (
        "pago para no generar intereses" in blob
        or "cargos, abonos y compras regulares" in blob
        or "producto: tarjeta de crédito" in blob
    )


def _parse_header(result: StatementParseResult, text: str, *, card: bool) -> None:
    period_span = re.search(
        rf"periodo:\s*(\d{{1,2}})\s+{MONTH_TOKEN}\s+(\d{{4}})\s+al\s+(\d{{1,2}})\s+{MONTH_TOKEN}\s+(\d{{4}})",
        text,
        re.IGNORECASE,
    )
    if period_span:
        result.period_start = _spanish_date(period_span.group(1), period_span.group(2), period_span.group(3))
        result.period_end = _spanish_date(period_span.group(4), period_span.group(5), period_span.group(6))
    else:
        period = re.search(
            r"periodo:\s*del\s+(\d{1,2})\s+al\s+(\d{1,2})\s+([a-záéíóú]+)\s+(\d{4})",
            text,
            re.IGNORECASE,
        )
        if period:
            result.period_start = _spanish_date(period.group(1), period.group(3), period.group(4))
            result.period_end = _spanish_date(period.group(2), period.group(3), period.group(4))
        else:
            slash = re.search(
                r"periodo(?:\s+del)?\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(?:al|a)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                text,
                re.IGNORECASE,
            )
            if slash:
                start_dt = _date(slash.group(1))
                end_dt = _date(slash.group(2))
                result.period_start = start_dt.date() if start_dt else None
                result.period_end = end_dt.date() if end_dt else None

    if card:
        closing = re.search(
            r"pago\s+para\s+no\s+generar\s+intereses\d*\s*[:=]?\s*" + AMOUNT,
            text,
            re.IGNORECASE,
        )
        previous = re.search(
            r"adeudo\s+del\s+periodo\s+anterior\s*=\s*" + AMOUNT,
            text,
            re.IGNORECASE,
        )
        minimum = re.search(
            r"pago\s+m[ií]nimo\d*\s*:\s*" + AMOUNT,
            text,
            re.IGNORECASE,
        )
        due = re.search(
            rf"fecha\s+l[ií]mite\s+de\s+pago\d*\s*:\s*(?:{WEEKDAYS})?,?\s*(\d{{1,2}})\s+{MONTH_TOKEN}\s+(\d{{4}})",
            text,
            re.IGNORECASE,
        )
        if due:
            result.due_date = _spanish_date(due.group(1), due.group(2), due.group(3))
    else:
        closing = re.search(
            r"(?:saldo\s+al\s+generar\s+este\s+estado\s+de\s+cuenta|saldo(?:\s+al)?\s+corte|saldo\s+nuevo|saldo\s+final)\s*:?\s*"
            + AMOUNT,
            text,
            re.IGNORECASE,
        )
        previous = re.search(
            r"(?:saldo\s+anterior|saldo\s+inicial)\s*:?\s*" + AMOUNT,
            text,
            re.IGNORECASE,
        )
        minimum = re.search(r"pago\s+m[ií]nimo\s*:?\s*" + AMOUNT, text, re.IGNORECASE)
        due = re.search(
            r"(?:fecha\s+l[ií]mite(?:\s+de\s+pago)?|paga\s+antes\s+del)\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            text,
            re.IGNORECASE,
        )
        if due:
            parsed = _date(due.group(1))
            result.due_date = parsed.date() if parsed else None

    if closing:
        result.closing_balance = _money(closing.group(1))
    if previous:
        result.previous_balance = _money(previous.group(1))
    if minimum:
        result.minimum_payment = _money(minimum.group(1))


def _parse_checking_lines(text: str) -> list[StatementLine]:
    lines: list[StatementLine] = []
    pending: list[str] = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        lowered = line.lower()
        if _should_skip(lowered):
            continue
        match = CHECKING_LINE.match(line)
        if match:
            parsed = _spanish_date(match.group(1), match.group(2), match.group(3))
            description = (match.group(4) or "").strip()
            if not description:
                description = " ".join(pending).strip() or "Movimiento"
            pending = []
            sign = match.group(5)
            amount = _money(match.group(6))
            lines.append(
                StatementLine(
                    date=parsed,
                    description=description[:200],
                    amount=amount,
                    kind=_kind(description, sign == "+", card=False),
                )
            )
            continue
        if CHECKING_LINE.search(line):
            pending = []
            continue
        if not _looks_like_noise(lowered):
            pending.append(line)
    return lines


def _parse_credit_card_lines(text: str) -> list[StatementLine]:
    lines: list[StatementLine] = []
    seen: list[tuple] = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        match = CARD_LINE.match(line)
        if not match:
            continue
        parsed = _spanish_date(match.group(1), match.group(2), match.group(3))
        description = re.sub(r"\s*\|\s*RFC:.*$", "", match.group(7), flags=re.IGNORECASE).strip()
        blob = description.lower()
        if any(token in blob for token in ("saldo revolvente", "crédito de saldo revolvente", "credito de saldo revolvente")):
            continue
        sign = match.group(8)
        amount = _money(match.group(9))
        kind = _card_kind(description, sign == "+")
        key = (parsed, description.lower(), amount, kind)
        if seen and seen[-1] == key:
            continue
        seen.append(key)
        lines.append(
            StatementLine(
                date=parsed,
                description=description[:200],
                amount=amount,
                kind=kind,
            )
        )
    return lines


def _parse_legacy_card_lines(text: str) -> list[StatementLine]:
    lines: list[StatementLine] = []
    for match in re.finditer(
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+" + AMOUNT,
        text,
    ):
        parsed = _date(match.group(1))
        description = re.sub(r"\s+", " ", match.group(2)).strip()
        if len(description) < 3:
            continue
        lowered = description.lower()
        if any(
            token in lowered
            for token in ("saldo", "periodo", "pago minimo", "pago mínimo", "fecha limite", "fecha límite")
        ):
            continue
        amount = _money(match.group(3))
        lines.append(
            StatementLine(
                date=parsed.date() if parsed else None,
                description=description[:200],
                amount=amount,
                kind=_kind(description, False, card=True),
            )
        )
    return lines


def _card_kind(description: str, is_charge: bool) -> str:
    blob = description.lower()
    if not is_charge:
        return "payment"
    if re.search(r"inter[eé]s", blob) or re.search(r"\biva\b", blob):
        return "fee"
    return "purchase"


def _kind(description: str, incoming: bool, *, card: bool = False) -> str:
    blob = description.lower()
    if incoming:
        return "income"
    if "pago a tu tarjeta" in blob or "pago tarjeta" in blob or "abono" in blob:
        return "payment"
    if card and "pago" in blob:
        return "payment"
    if "comisi" in blob:
        return "fee"
    if "transferencia" in blob:
        return "transfer"
    return "purchase"


def _should_skip(lowered: str) -> bool:
    if re.fullmatch(r"\d+\s+de\s+\d+", lowered):
        return True
    return any(lowered.startswith(prefix) for prefix in SKIP_PREFIXES)


def _looks_like_noise(lowered: str) -> bool:
    if _should_skip(lowered):
        return True
    if any(
        token in lowered
        for token in (
            "clave de rastreo",
            "clave de referencia",
            "dato no verificado",
            "monto en pesos",
            "alcaldia",
            "alcaldía",
        )
    ):
        return True
    if not re.search(r"\d", lowered) and not any(
        token in lowered for token in ("transferencia", "compra", "pago", "retiro", "deposito", "depósito")
    ):
        return True
    return False
