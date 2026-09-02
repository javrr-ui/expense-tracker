"""Infer a finer transaction kind from type + description."""

from __future__ import annotations

from unidecode import unidecode

from models.transaction import Transaction

VALID_KINDS = frozenset({"purchase", "payment", "transfer", "income", "fee"})

PAYMENT_HINTS = (
    "pago didi",
    "pago de rappi",
    "pago rappicard",
    "pago tarjeta",
    "recibimos tu pago",
    "pago de tarjeta",
    "abono",
)

TRANSFER_HINTS = (
    "transferencia",
    "spei",
    "envio spei",
)


def normalize(value: str | None) -> str:
    if not value:
        return ""
    return unidecode(value).lower().strip()


def infer_kind(tx: Transaction) -> str:
    if tx.kind and tx.kind in VALID_KINDS:
        return tx.kind
    if tx.type == "income":
        return "income"
    blob = f"{normalize(tx.merchant)} {normalize(tx.description)}"
    if any(hint in blob for hint in PAYMENT_HINTS):
        return "payment"
    if any(hint in blob for hint in TRANSFER_HINTS):
        return "transfer"
    return "purchase"
