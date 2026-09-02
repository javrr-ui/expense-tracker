"""Match statement lines to existing email/manual ledger rows."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from unidecode import unidecode

from models.transaction import Transaction

PAYMENT_TOKENS = frozenset({"tarjeta", "gracias", "abono"})
GENERIC_DESC = frozenset({"transferencia", "compra", "movimiento", "pago"})


def _norm(value: str | None) -> str:
    return unidecode(value or "").lower()


def _tokens(value: str | None) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", _norm(value)))


def _tx_date(tx: Transaction) -> date | None:
    if tx.date is None:
        return None
    value = tx.date
    if value.tzinfo is not None:
        value = value.replace(tzinfo=None)
    return value.date()


def match_score(statement_tx: Transaction, ledger_tx: Transaction) -> int:
    """Higher is better. Negative means no match."""
    if abs(float(statement_tx.amount) - float(ledger_tx.amount)) >= 0.02:
        return -1
    stmt_day = _tx_date(statement_tx)
    led_day = _tx_date(ledger_tx)
    if stmt_day is None or led_day is None:
        date_score = 0
    else:
        days = abs((stmt_day - led_day).days)
        if days > 2:
            return -1
        date_score = 3 - days
    stmt_tokens = _tokens(statement_tx.description) | _tokens(statement_tx.merchant)
    led_tokens = _tokens(ledger_tx.description) | _tokens(ledger_tx.merchant)
    overlap = len(stmt_tokens & led_tokens)
    stmt_pay = bool(stmt_tokens & PAYMENT_TOKENS) or statement_tx.kind == "payment"
    led_pay = bool(led_tokens & PAYMENT_TOKENS) or ledger_tx.kind == "payment"
    if stmt_pay and led_pay:
        overlap += 3
    elif stmt_pay != led_pay:
        return -1
    if "transferencia" in stmt_tokens and "transferencia" in led_tokens:
        overlap += 1
    led_generic = _norm(ledger_tx.description).strip() in GENERIC_DESC
    if overlap == 0:
        if led_generic and not stmt_pay and not led_pay:
            overlap = 1
        else:
            return -1
    return date_score * 10 + overlap


def pair_matches(
    statement_txs: list[Transaction],
    ledger_txs: list[Transaction],
) -> list[tuple[Transaction, Transaction, int]]:
    """Greedy unique pairing by descending score."""
    scored: list[tuple[int, int, int, int]] = []
    for s_idx, stmt in enumerate(statement_txs):
        for l_idx, led in enumerate(ledger_txs):
            score = match_score(stmt, led)
            if score >= 10:
                scored.append((score, s_idx, l_idx, id(stmt)))
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    used_s: set[int] = set()
    used_l: set[int] = set()
    pairs: list[tuple[Transaction, Transaction, int]] = []
    for score, s_idx, l_idx, _ in scored:
        if s_idx in used_s or l_idx in used_l:
            continue
        used_s.add(s_idx)
        used_l.add(l_idx)
        pairs.append((statement_txs[s_idx], ledger_txs[l_idx], score))
    return pairs


def ledger_window(period_start: date | None, period_end: date | None) -> tuple[datetime | None, datetime | None]:
    start = datetime.combine(period_start - timedelta(days=2), datetime.min.time()) if period_start else None
    end = datetime.combine(period_end + timedelta(days=2), datetime.max.time()) if period_end else None
    return start, end


def should_enrich_description(ledger: Transaction, statement: Transaction) -> bool:
    led = _norm(ledger.description).strip()
    stmt = (statement.description or "").strip()
    if not stmt:
        return False
    if not led or led in GENERIC_DESC:
        return True
    return len(stmt) > len(ledger.description or "") + 8
