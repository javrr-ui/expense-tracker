"""Pick an account for a transaction based on bank + kind + hints."""

from __future__ import annotations

from sqlmodel import Session, col, select

from constants.account_types import ASSET_ACCOUNT_TYPES, LIABILITY_ACCOUNT_TYPES
from models.account import Account
from models.account_type import AccountType
from models.transaction import Transaction
from unidecode import unidecode


def resolve_account(session: Session, tx: Transaction) -> Account | None:
    """Return the unique matching active account, or None if ambiguous/missing."""
    rows = session.exec(
        select(Account, AccountType)
        .join(AccountType, col(AccountType.id) == col(Account.account_type_id))
        .where(Account.bank_id == tx.bank_id, col(Account.is_active) == True)  # noqa: E712
    ).all()
    if not rows:
        return None
    if len(rows) == 1:
        return rows[0][0]

    kind = tx.kind or ""
    blob = unidecode(f"{tx.merchant or ''} {tx.description or ''}").lower()

    preferred: set[str]
    if kind == "payment" or "credito" in blob or "préstamo" in blob or "prestamo" in blob:
        preferred = set(LIABILITY_ACCOUNT_TYPES)
        if "prestamo" in blob or "préstamo" in blob:
            preferred = {"loan"}
        elif "credito" in blob or "rappi" in blob:
            preferred = {"credit_card"}
    elif kind in {"transfer", "income"} or "debito" in blob:
        preferred = set(ASSET_ACCOUNT_TYPES)
    elif kind == "purchase":
        if "credito" in blob:
            preferred = {"credit_card"}
        elif "debito" in blob:
            preferred = set(ASSET_ACCOUNT_TYPES)
        else:
            preferred = set()
    else:
        preferred = set()

    if preferred:
        filtered = [account for account, account_type in rows if account_type.name in preferred]
        if len(filtered) == 1:
            return filtered[0]
        if len(filtered) > 1:
            return None

    return None
