"""Tests for kind inference and notes/tags updates."""

from contextlib import contextmanager
from datetime import datetime

from core.services.transaction_kind import infer_kind
from core.services.transaction_service import TransactionService
from database.database import Database
from models.transaction import Transaction, TransactionCreate, TransactionUpdate


@contextmanager
def _svc():
    db = Database("sqlite://")
    try:
        yield TransactionService(db)
    finally:
        db.close()


def test_infer_payment_and_transfer():
    payment = Transaction(
        bank_id=1,
        email_id="a",
        amount=100,
        description="Pago DiDi Préstamos",
        type="expense",
        merchant="DiDi Préstamos",
    )
    transfer = Transaction(
        bank_id=1,
        email_id="b",
        amount=200,
        description="Transferencia exitosa",
        type="expense",
    )
    income = Transaction(
        bank_id=1,
        email_id="c",
        amount=50,
        description="Depósito",
        type="income",
    )
    assert infer_kind(payment) == "payment"
    assert infer_kind(transfer) == "transfer"
    assert infer_kind(income) == "income"


def test_save_sets_kind_and_update_writes_notes_tags():
    with _svc() as service:
        tx_id = service.save_transaction(
            TransactionCreate(
                email_id="n1",
                bank_name="hey_banco",
                amount=200,
                description="Transferencia SPEI",
                type="expense",
                date=datetime(2026, 9, 1),
            )
        )
        assert tx_id is not None
        tx = service.get_transaction(tx_id)
        assert tx is not None
        assert tx["kind"] == "transfer"

        updated = service.update_transaction(
            tx_id,
            TransactionUpdate(notes="Cooperación kermés del trabajo", tags=["kermes", "trabajo"]),
        )
        assert updated["notes"] == "Cooperación kermés del trabajo"
        assert updated["tags"] == ["kermes", "trabajo"]
