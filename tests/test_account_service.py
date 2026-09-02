"""Tests for account CRUD, snapshots, and dashboard totals."""

from contextlib import contextmanager
from datetime import date, datetime

from constants.account_types import AccountTypeName
from core.services.account_service import AccountService
from database.database import Database
from models.account import AccountCreate, AccountUpdate, BalanceUpdate


@contextmanager
def _service():
    db = Database("sqlite://")
    try:
        yield AccountService(db)
    finally:
        db.close()


def _create(service: AccountService, **overrides) -> dict:
    payload = {
        "name": "Nu Crédito",
        "bank_name": "nubank",
        "account_type": AccountTypeName.CREDIT_CARD,
        "current_balance": 12400,
        "credit_limit": 50000,
        "due_date_day": 15,
        "last_four": "4412",
    }
    payload.update(overrides)
    return service.create_account(AccountCreate(**payload)).model_dump()


def test_create_account_records_opening_snapshot():
    with _service() as service:
        account = _create(service)

    assert account["current_balance"] == 12400
    assert account["is_liability"] is True
    assert account["bank_display_name"] == "Nu"
    assert account["has_statement_password"] is False
    assert account["utilization"] == 0.248
    assert len(account["snapshots"]) == 1
    assert account["snapshots"][0]["source"] == "manual"
    assert account["last_snapshot_at"] is not None


def test_dashboard_splits_assets_and_liabilities():
    with _service() as service:
        _create(service, name="Nu Crédito", current_balance=10000, credit_limit=40000)
        _create(
            service,
            name="Hey Débito",
            bank_name="hey_banco",
            account_type=AccountTypeName.CHECKING,
            current_balance=3500,
            credit_limit=None,
            due_date_day=None,
            last_four=None,
        )
        _create(
            service,
            name="Rappi",
            bank_name="rappi",
            account_type=AccountTypeName.CREDIT_CARD,
            current_balance=2000,
            credit_limit=15000,
        )

        dashboard = service.get_dashboard()
        assert dashboard.total_debt == 12000
        assert dashboard.total_assets == 3500
        assert dashboard.net_position == -8500
        assert len(dashboard.liability_accounts) == 2
        assert len(dashboard.asset_accounts) == 1


def test_set_balance_adds_snapshot_and_updates_current():
    with _service() as service:
        created = _create(service, current_balance=5000)
        updated = service.set_balance(
            created["id"],
            BalanceUpdate(amount=4200, note="Revisión del app"),
        )
        assert updated.current_balance == 4200
        assert len(updated.snapshots) == 2
        assert updated.snapshots[0].amount == 4200
        assert updated.snapshots[0].note == "Revisión del app"


def test_duplicate_name_raises():
    with _service() as service:
        _create(service, name="Nu")
        try:
            _create(service, name="Nu")
            assert False, "expected ValueError"
        except ValueError as extra:
            assert "existe" in str(extra).lower()


def test_unknown_account_type_raises():
    with _service() as service:
        try:
            _create(service, account_type="crypto")
            assert False, "expected ValueError"
        except ValueError as extra:
            assert "desconocido" in str(extra).lower()


def test_update_does_not_change_balance():
    with _service() as service:
        created = _create(service, current_balance=8000)
        updated = service.update_account(
            created["id"],
            AccountUpdate(name="Nu Clásica", apr=72.5),
        )
        assert updated.name == "Nu Clásica"
        assert updated.apr == 72.5
        assert updated.current_balance == 8000


def test_inactive_accounts_are_hidden_from_dashboard():
    with _service() as service:
        created = _create(service, current_balance=9000)
        service.update_account(created["id"], AccountUpdate(is_active=False))
        dashboard = service.get_dashboard()
        assert dashboard.total_debt == 0
        assert dashboard.liability_accounts == []


def test_statement_password_is_never_serialized():
    with _service() as service:
        account = _create(service, statement_password="RFC123")
        assert account["has_statement_password"] is True
        assert "statement_password" not in account


def test_next_due_date_rolls_to_next_month():
    due = AccountService._next_due_date(15, today=date(2026, 8, 20))
    assert due == "2026-09-15"
    due_same = AccountService._next_due_date(20, today=date(2026, 8, 20))
    assert due_same == "2026-08-20"
    due_feb = AccountService._next_due_date(31, today=date(2026, 2, 1))
    assert due_feb == "2026-02-28"


def test_last_four_must_be_four_digits():
    try:
        AccountCreate(
            name="Bad",
            bank_name="nubank",
            account_type="credit_card",
            last_four="12",
        )
        assert False, "expected validation error"
    except Exception:
        pass


def test_get_missing_account_returns_none():
    with _service() as service:
        assert service.get_account(999) is None


def test_list_bank_options_includes_known_and_extra_banks():
    with _service() as service:
        _create(service, bank_name="banco_inventado", name="Cuenta rara")
        names = {option.name for option in service.list_bank_options()}
        assert "nubank" in names
        assert "banco_inventado" in names


def test_opening_snapshot_timestamp_is_naive():
    with _service() as service:
        account = _create(service)
        as_of = account["snapshots"][0]["as_of"]
        assert isinstance(as_of, datetime)
        assert as_of.tzinfo is None


def test_loan_biweekly_recurrence_lists_future_dates(monkeypatch):
    class FakeDate(date):
        @classmethod
        def today(cls):
            return date(2026, 9, 1)

    monkeypatch.setattr("core.services.account_service.date", FakeDate)

    with _service() as service:
        created = _create(
            service,
            name="DiDi Prestamo",
            bank_name="didi",
            account_type=AccountTypeName.LOAN,
            current_balance=18000,
            credit_limit=None,
            last_four=None,
            due_date_day=None,
            minimum_payment=1500,
            payment_frequency="biweekly",
            recurrence_anchor=date(2026, 9, 4),
            remaining_payments=6,
        )
        dates = [item["date"] for item in created["scheduled_payments"]]
        assert created["payment_frequency"] == "biweekly"
        assert created["next_due_date"] == "2026-08-21"
        assert dates[:3] == ["2026-08-21", "2026-09-04", "2026-09-18"]
        assert len(dates) == 6

        dashboard = service.get_dashboard()
        loan_dues = [
            item
            for item in dashboard.upcoming_payments
            if item.account_name == "DiDi Prestamo"
        ]
        assert loan_dues[0].due_date == "2026-08-21"
        assert loan_dues[0].status == "overdue"
        assert loan_dues[1].due_date == "2026-09-04"


def test_mark_minimum_paid_stops_overdue(monkeypatch):
    from models.payment_coverage import PaymentCoverageUpsert

    class FakeDate(date):
        @classmethod
        def today(cls):
            return date(2026, 9, 1)

    monkeypatch.setattr("core.services.account_service.date", FakeDate)

    with _service() as service:
        created = _create(
            service,
            name="Nu Card",
            due_date_day=15,
            minimum_payment=200,
        )
        overdue = created["scheduled_payments"][0]["date"]
        assert overdue < "2026-09-01"
        service.set_payment_coverage(
            created["id"],
            PaymentCoverageUpsert(due_date=date.fromisoformat(overdue), status="minimum_paid"),
        )
        dashboard = service.get_dashboard()
        assert all(
            not (payment.account_id == created["id"] and payment.due_date == overdue)
            for payment in dashboard.upcoming_payments
        )
        detail = service.get_account(created["id"])
        assert detail is not None
        assert detail.next_due_date != overdue
        assert detail.scheduled_payments[0].coverage == "minimum_paid"
