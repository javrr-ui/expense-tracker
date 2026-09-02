"""Apply a transaction's signed effect to an account balance once."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session

from constants.account_types import is_liability_type
from core.services.transaction_kind import infer_kind
from models.account import Account
from models.account_type import AccountType
from models.transaction import Transaction


def _book_amount(tx: Transaction) -> float:
    currency = (getattr(tx, "currency", None) or "MXN").upper()
    if currency == "MXN":
        return abs(float(tx.amount or 0))
    mxn = getattr(tx, "amount_mxn", None)
    return abs(float(mxn)) if mxn else 0.0


def signed_amount(tx: Transaction, liability: bool) -> float:
    kind = tx.kind or infer_kind(tx)
    amount = _book_amount(tx)
    if liability:
        if kind in {"payment", "income"} or tx.type == "income":
            return -amount
        return amount
    if kind == "income" or tx.type == "income":
        return amount
    return -amount


def should_apply(tx: Transaction, account: Account) -> bool:
    if tx.account_id is None or tx.balance_applied:
        return False
    if _book_amount(tx) <= 0:
        return False
    if account.last_snapshot_at is None:
        return True
    if tx.date is None:
        return False
    tx_date = tx.date
    if tx_date.tzinfo is not None:
        tx_date = tx_date.replace(tzinfo=None)
    snapshot = account.last_snapshot_at
    if snapshot.tzinfo is not None:
        snapshot = snapshot.replace(tzinfo=None)
    return tx_date > snapshot


def apply_if_needed(session: Session, tx: Transaction) -> bool:
    """Mutate account.current_balance. Returns True if applied."""
    if tx.account_id is None or tx.balance_applied:
        return False
    account = session.get(Account, tx.account_id)
    if account is None:
        return False
    if not should_apply(tx, account):
        return False
    account_type = session.get(AccountType, account.account_type_id)
    liability = is_liability_type(account_type.name) if account_type else False
    delta = signed_amount(tx, liability)
    new_balance = account.current_balance + delta
    if liability:
        new_balance = max(0.0, new_balance)
    account.current_balance = round(new_balance, 2)
    account.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    tx.balance_applied = True
    session.add(account)
    session.add(tx)
    return True


def reverse_if_applied(session: Session, tx: Transaction) -> None:
    """Undo a previously applied delta (delete/reassign)."""
    if not tx.balance_applied or tx.account_id is None:
        return
    account = session.get(Account, tx.account_id)
    if account is None:
        tx.balance_applied = False
        return
    account_type = session.get(AccountType, account.account_type_id)
    liability = is_liability_type(account_type.name) if account_type else False
    delta = signed_amount(tx, liability)
    new_balance = account.current_balance - delta
    if liability:
        new_balance = max(0.0, new_balance)
    account.current_balance = round(new_balance, 2)
    tx.balance_applied = False
    session.add(account)
    session.add(tx)
