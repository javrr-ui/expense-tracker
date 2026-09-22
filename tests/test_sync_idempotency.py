"""AC coverage for expense-tracker #46 (cron sync MVP).

AC2: same email_id twice → no double transaction
AC3: unknown sender → no parser (pipeline continues; covered at helper level)
AC4: fixtures/in-memory DB only — no Gmail live
"""

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from core.parsers.parser_helper import ParserHelper
from core.services.transaction_service import TransactionService
from database.database import Database
from models.transaction import Transaction, TransactionCreate
from sqlmodel import select


@contextmanager
def _svc():
    db = Database("sqlite://")
    try:
        yield TransactionService(db), db
    finally:
        db.close()


def _tx(email_id: str, amount: float = 100.0) -> TransactionCreate:
    return TransactionCreate(
        email_id=email_id,
        bank_name="banamex",
        amount=amount,
        description="Compra test fixture",
        type="expense",
        date=datetime(2026, 9, 21, 12, 0, 0),
        merchant="FIXTURE STORE",
        reference="ref-1",
    )


def test_ac2_same_email_id_is_idempotent():
    with _svc() as (service, db):
        first = service.save_transaction(_tx("gmail-msg-abc"))
        second = service.save_transaction(_tx("gmail-msg-abc", amount=999.0))
        assert first is not None
        assert second is None
        with db.session() as session:
            rows = list(
                session.exec(
                    select(Transaction).where(Transaction.email_id == "gmail-msg-abc")
                )
            )
        assert len(rows) == 1
        assert rows[0].amount == 100.0


def test_ac2_distinct_email_ids_create_two_rows():
    with _svc() as (service, db):
        a = service.save_transaction(_tx("gmail-msg-1"))
        b = service.save_transaction(_tx("gmail-msg-2"))
        assert a is not None and b is not None
        with db.session() as session:
            count = len(list(session.exec(select(Transaction))))
        assert count == 2


def test_ac3_unknown_sender_has_no_parser():
    parser = ParserHelper.get_parser_for_email("noreply@random-promo.example")
    assert parser is None


def test_ac4_suite_uses_in_memory_db_not_live_gmail():
    # Guardrail: this module must not import live Gmail clients.
    import tests.test_sync_idempotency as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "googleapiclient" not in src
    assert "get_gmail_service" not in src
