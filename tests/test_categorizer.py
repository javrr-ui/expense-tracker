"""Tests for category seed, rules, manual lock, and spending stats."""

from contextlib import contextmanager
from datetime import datetime

from core.services.categorizer import Categorizer
from core.services.category_service import CategoryService
from core.services.transaction_service import TransactionService
from database.database import Database
from models.transaction import TransactionCategoryUpdate, TransactionCreate


@contextmanager
def _db():
    db = Database("sqlite://")
    try:
        yield db
    finally:
        db.close()


def _save(service: TransactionService, **overrides) -> int:
    payload = {
        "email_id": overrides.pop("email_id", "e1"),
        "bank_name": "hey_banco",
        "amount": 100.0,
        "description": "OXXO INSURGENTES",
        "type": "expense",
        "merchant": "OXXO",
        "date": datetime(2026, 9, 1, 12, 0, 0),
    }
    payload.update(overrides)
    tx_id = service.save_transaction(TransactionCreate(**payload))
    assert tx_id is not None
    return tx_id


def test_seed_creates_categories_and_rules():
    with _db() as db:
        tree = CategoryService(db).list_tree()
        names = {item.name for item in tree}
        assert "Comida" in names
        assert "Deudas" in names
        comida = next(item for item in tree if item.name == "Comida")
        assert any(sub.name == "Super" for sub in comida.subcategories)


def test_oxxo_is_auto_comida_super():
    with _db() as db:
        service = TransactionService(db)
        tx_id = _save(service)
        tx = service.get_transaction(tx_id)
        assert tx is not None
        assert tx["category_name"] == "Comida"
        assert tx["subcategory_name"] == "Super"
        assert tx["category_source"] == "auto"
        assert tx["category_locked"] is False


def test_didi_loan_payment_is_deuda():
    with _db() as db:
        service = TransactionService(db)
        tx_id = _save(
            service,
            email_id="didi-1",
            bank_name="didi",
            description="Pago DiDi Préstamos · siguiente: 2026-08-28",
            merchant="DiDi Préstamos",
            amount=1780.54,
        )
        tx = service.get_transaction(tx_id)
        assert tx is not None
        assert tx["category_name"] == "Deudas"
        assert tx["subcategory_name"] == "Pago préstamo"


def test_manual_assign_locks_and_teaches_merchant_rule():
    with _db() as db:
        service = TransactionService(db)
        first = _save(service, email_id="m1", merchant="FOO CAFE", description="FOO CAFE")
        comida = next(item for item in CategoryService(db).list_tree() if item.name == "Comida")
        cafe = next(sub for sub in comida.subcategories if sub.name == "Café")
        updated = service.assign_category(
            first,
            TransactionCategoryUpdate(category_id=comida.id, subcategory_id=cafe.id),
        )
        assert updated["category_name"] == "Comida"
        assert updated["category_locked"] is True
        assert updated["category_source"] == "manual"

        second = _save(service, email_id="m2", merchant="FOO CAFE", description="FOO CAFE Tlalpan")
        learned = service.get_transaction(second)
        assert learned is not None
        assert learned["category_name"] == "Comida"
        assert learned["subcategory_name"] == "Café"


def test_locked_transaction_skips_recategorize():
    with _db() as db:
        service = TransactionService(db)
        tx_id = _save(service, email_id="lock-1", merchant="OXXO", description="OXXO")
        comida = next(item for item in CategoryService(db).list_tree() if item.name == "Comida")
        delivery = next(sub for sub in comida.subcategories if sub.name == "Delivery")
        service.assign_category(
            tx_id,
            TransactionCategoryUpdate(category_id=comida.id, subcategory_id=delivery.id),
        )
        result = service.recategorize()
        assert result["skipped_locked"] >= 1
        tx = service.get_transaction(tx_id)
        assert tx is not None
        assert tx["subcategory_name"] == "Delivery"


def test_spending_stats_group_by_category():
    with _db() as db:
        txs = TransactionService(db)
        _save(txs, email_id="s1", merchant="OXXO", description="OXXO", amount=50)
        _save(txs, email_id="s2", merchant="OXXO", description="OXXO", amount=25)
        stats = CategoryService(db).spending_by_category()
        assert stats["total"] == 75
        comida = next(item for item in stats["categories"] if item["category_name"] == "Comida")
        assert comida["amount"] == 75
