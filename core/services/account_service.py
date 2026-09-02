"""Account and dashboard service.

Keeps all balance and account logic on the server so the web UI and a future
mobile app can share the same JSON contract.
"""

from __future__ import annotations

import calendar
import logging
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import col, desc, select

from constants.account_types import (
    ACCOUNT_TYPE_SEED,
    LIABILITY_ACCOUNT_TYPES,
    is_liability_type,
)
from constants.banks import BANK_DISPLAY_NAMES, SupportedBanks, bank_display_name
from constants.payment_frequency import PAYMENT_FREQUENCY_LABELS
from core.services.payment_schedule import upcoming_payment_dates
from database.database import Database
from models.account import (
    Account,
    AccountCreate,
    AccountDetail,
    AccountRead,
    AccountTypeRead,
    AccountUpdate,
    BalanceSnapshotRead,
    BalanceUpdate,
    BankOption,
    DashboardRead,
    ScheduledPayment,
    UpcomingPayment,
)
from models.account_type import AccountType
from models.balance_snapshot import BalanceSnapshot
from models.bank import Bank
from models.payment_coverage import VALID_COVERAGE, PaymentCoverage, PaymentCoverageUpsert, utc_now as coverage_now

logger = logging.getLogger("expense_tracker")


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AccountService:
    """CRUD for accounts, manual balance snapshots, and dashboard aggregates."""

    def __init__(self, db: Database):
        self.db = db

    def list_account_types(self) -> list[AccountTypeRead]:
        return [
            AccountTypeRead(
                name=name,
                label=label,
                is_liability=is_liability_type(name),
            )
            for name, label in ACCOUNT_TYPE_SEED
        ]

    def list_bank_options(self) -> list[BankOption]:
        known = [
            BankOption(name=bank.value, display_name=BANK_DISPLAY_NAMES[bank])
            for bank in SupportedBanks
        ]
        known_names = {option.name for option in known}
        with self.db.session() as session:
            extra_names = [bank.name for bank in session.exec(select(Bank)).all()]
        for name in extra_names:
            if name not in known_names:
                known.append(BankOption(name=name, display_name=bank_display_name(name)))
                known_names.add(name)
        return known

    def list_accounts(self, active_only: bool = False) -> list[AccountRead]:
        with self.db.session() as session:
            rows = self._load_account_rows(session, active_only=active_only)
            coverages = self._coverages_map(session, [account.id for account, _b, _t in rows if account.id])
            return [
                self._to_read(account, bank, account_type, coverages.get(account.id or 0, {}))
                for account, bank, account_type in rows
            ]

    def get_account(self, account_id: int) -> Optional[AccountDetail]:
        with self.db.session() as session:
            row = self._get_row(session, account_id)
            if row is None:
                return None
            account, bank, account_type = row
            snapshots = session.exec(
                select(BalanceSnapshot)
                .where(BalanceSnapshot.account_id == account_id)
                .order_by(desc(col(BalanceSnapshot.as_of)), desc(col(BalanceSnapshot.id)))
                .limit(20)
            ).all()
            coverages = self._coverages_map(session, [account_id])
            return AccountDetail(
                **self._to_read(account, bank, account_type, coverages.get(account_id, {})).model_dump(),
                snapshots=[
                    BalanceSnapshotRead(
                        id=snapshot.id,  # type: ignore[arg-type]
                        amount=snapshot.amount,
                        as_of=snapshot.as_of,
                        source=snapshot.source,
                        note=snapshot.note,
                    )
                    for snapshot in snapshots
                    if snapshot.id is not None
                ],
            )

    def create_account(self, data: AccountCreate) -> AccountDetail:
        with self.db.session() as session:
            account_type = self._get_account_type(session, data.account_type)
            bank = self._get_or_create_bank(session, data.bank_name)
            now = utc_now()
            account = Account(
                bank_id=bank.id,  # type: ignore[arg-type]
                name=data.name,
                account_number=data.account_number,
                account_type_id=account_type.id,  # type: ignore[arg-type]
                current_balance=data.current_balance,
                currency=data.currency.upper(),
                apr=data.apr,
                minimum_payment=data.minimum_payment,
                due_date_day=data.due_date_day,
                cutoff_date_day=data.cutoff_date_day,
                last_four=data.last_four,
                credit_limit=data.credit_limit,
                is_active=True,
                last_snapshot_at=now,
                statement_password=data.statement_password,
                payment_frequency=data.payment_frequency,
                recurrence_anchor=data.recurrence_anchor,
                recurrence_end=data.recurrence_end,
                remaining_payments=data.remaining_payments,
                created_at=now,
                updated_at=now,
            )
            session.add(account)
            try:
                session.flush()
            except IntegrityError as exc:
                raise ValueError("Ya existe una cuenta con ese nombre o número") from exc

            snapshot = BalanceSnapshot(
                account_id=account.id,  # type: ignore[arg-type]
                amount=data.current_balance,
                as_of=now,
                source="manual",
                note="Saldo inicial",
            )
            session.add(snapshot)
            session.flush()
            logger.info(
                "Account created [ID: %s] %s balance=%s",
                account.id,
                account.name,
                account.current_balance,
            )
            return self._detail_from_session(session, account.id)  # type: ignore[arg-type]

    def update_account(self, account_id: int, data: AccountUpdate) -> AccountDetail:
        payload = data.model_dump(exclude_unset=True)
        with self.db.session() as session:
            account = session.get(Account, account_id)
            if account is None:
                raise LookupError("Account not found")

            if "bank_name" in payload:
                bank = self._get_or_create_bank(session, payload.pop("bank_name"))
                account.bank_id = bank.id  # type: ignore[assignment]

            if "account_type" in payload:
                account_type = self._get_account_type(session, payload.pop("account_type"))
                account.account_type_id = account_type.id  # type: ignore[assignment]

            if "currency" in payload and payload["currency"]:
                payload["currency"] = payload["currency"].upper()

            for field, value in payload.items():
                setattr(account, field, value)

            account.updated_at = utc_now()
            session.add(account)
            try:
                session.flush()
            except IntegrityError as exc:
                raise ValueError("Ya existe una cuenta con ese nombre o número") from exc
            return self._detail_from_session(session, account_id)

    def set_balance(self, account_id: int, data: BalanceUpdate) -> AccountDetail:
        as_of = data.as_of or utc_now()
        if as_of.tzinfo is not None:
            as_of = as_of.replace(tzinfo=None)

        with self.db.session() as session:
            account = session.get(Account, account_id)
            if account is None:
                raise LookupError("Account not found")

            account.current_balance = data.amount
            account.last_snapshot_at = as_of
            account.updated_at = utc_now()
            session.add(account)
            session.add(
                BalanceSnapshot(
                    account_id=account_id,
                    amount=data.amount,
                    as_of=as_of,
                    source="manual",
                    note=data.note,
                )
            )
            session.flush()
            logger.info(
                "Balance snapshot [account %s] amount=%s as_of=%s",
                account_id,
                data.amount,
                as_of,
            )
            return self._detail_from_session(session, account_id)

    def get_dashboard(self) -> DashboardRead:
        accounts = self.list_accounts(active_only=True)
        liabilities = [account for account in accounts if account.is_liability]
        assets = [account for account in accounts if not account.is_liability]
        total_debt = round(sum(account.current_balance for account in liabilities), 2)
        total_assets = round(sum(account.current_balance for account in assets), 2)
        upcoming: list[UpcomingPayment] = []
        today = date.today()
        for account in liabilities:
            for occurrence in account.scheduled_payments:
                due = date.fromisoformat(occurrence.date)
                delta_days = (due - today).days
                coverage = occurrence.coverage
                if coverage in VALID_COVERAGE:
                    continue
                if delta_days < 0:
                    status = "overdue"
                elif delta_days <= 3:
                    status = "due_soon"
                else:
                    status = "upcoming"
                upcoming.append(
                    UpcomingPayment(
                        account_id=account.id,
                        account_name=account.name,
                        bank_display_name=account.bank_display_name,
                        amount=occurrence.amount,
                        due_date=occurrence.date,
                        status=status,
                    )
                )
        upcoming.sort(key=lambda item: item.due_date)
        upcoming = upcoming[:16]
        return DashboardRead(
            total_debt=total_debt,
            total_assets=total_assets,
            net_position=round(total_assets - total_debt, 2),
            liability_accounts=liabilities,
            asset_accounts=assets,
            upcoming_payments=upcoming,
        )

    def _detail_from_session(self, session, account_id: int) -> AccountDetail:
        row = self._get_row(session, account_id)
        if row is None:
            raise LookupError("Account not found")
        account, bank, account_type = row
        snapshots = session.exec(
            select(BalanceSnapshot)
            .where(BalanceSnapshot.account_id == account_id)
            .order_by(desc(col(BalanceSnapshot.as_of)), desc(col(BalanceSnapshot.id)))
            .limit(20)
        ).all()
        coverages = self._coverages_map(session, [account_id])
        return AccountDetail(
            **self._to_read(account, bank, account_type, coverages.get(account_id, {})).model_dump(),
            snapshots=[
                BalanceSnapshotRead(
                    id=snapshot.id,  # type: ignore[arg-type]
                    amount=snapshot.amount,
                    as_of=snapshot.as_of,
                    source=snapshot.source,
                    note=snapshot.note,
                )
                for snapshot in snapshots
                if snapshot.id is not None
            ],
        )

    @staticmethod
    def _load_account_rows(session, active_only: bool = False):
        stmt = (
            select(Account, Bank, AccountType)
            .join(Bank, col(Bank.id) == col(Account.bank_id))
            .join(AccountType, col(AccountType.id) == col(Account.account_type_id))
        )
        if active_only:
            stmt = stmt.where(col(Account.is_active) == True)  # noqa: E712
        stmt = stmt.order_by(col(Account.is_active).desc(), col(Account.name))
        return session.exec(stmt).all()

    @staticmethod
    def _get_row(session, account_id: int):
        stmt = (
            select(Account, Bank, AccountType)
            .join(Bank, col(Bank.id) == col(Account.bank_id))
            .join(AccountType, col(AccountType.id) == col(Account.account_type_id))
            .where(Account.id == account_id)
        )
        return session.exec(stmt).first()

    @staticmethod
    def _get_account_type(session, type_name: str) -> AccountType:
        account_type = session.exec(
            select(AccountType).where(AccountType.name == type_name)
        ).first()
        if account_type is None:
            raise ValueError(f"Tipo de cuenta desconocido: {type_name}")
        return account_type

    @staticmethod
    def _get_or_create_bank(session, bank_name: str) -> Bank:
        bank = session.exec(select(Bank).where(Bank.name == bank_name)).first()
        if bank is None:
            bank = Bank(name=bank_name)
            session.add(bank)
            session.flush()
        if bank.id is None:
            raise ValueError(f"No se pudo guardar el banco: {bank_name}")
        return bank

    @staticmethod
    def _next_due_date(due_day: Optional[int], today: Optional[date] = None) -> Optional[str]:
        if due_day is None:
            return None
        today = today or date.today()

        def clamp(year: int, month: int, day: int) -> date:
            last = calendar.monthrange(year, month)[1]
            return date(year, month, min(day, last))

        candidate = clamp(today.year, today.month, due_day)
        if candidate < today:
            if today.month == 12:
                candidate = clamp(today.year + 1, 1, due_day)
            else:
                candidate = clamp(today.year, today.month + 1, due_day)
        return candidate.isoformat()

    def set_payment_coverage(self, account_id: int, payload: PaymentCoverageUpsert) -> AccountDetail:
        status = payload.status
        if status is not None and status not in VALID_COVERAGE:
            raise ValueError("Estado inválido. Usa minimum_paid, paid_in_full o vacío para quitarlo.")
        with self.db.session() as session:
            account = session.get(Account, account_id)
            if account is None:
                raise LookupError("Account not found")
            existing = session.exec(
                select(PaymentCoverage).where(
                    PaymentCoverage.account_id == account_id,
                    PaymentCoverage.due_date == payload.due_date,
                )
            ).first()
            if not status:
                if existing is not None:
                    session.delete(existing)
            elif existing is not None:
                existing.status = status
                existing.note = payload.note
                existing.updated_at = coverage_now()
                session.add(existing)
            else:
                session.add(
                    PaymentCoverage(
                        account_id=account_id,
                        due_date=payload.due_date,
                        status=status,
                        note=payload.note,
                    )
                )
            session.flush()
            return self._detail_from_session(session, account_id)

    @staticmethod
    def _coverages_map(session, account_ids: list[int]) -> dict[int, dict[str, str]]:
        if not account_ids:
            return {}
        rows = session.exec(
            select(PaymentCoverage).where(col(PaymentCoverage.account_id).in_(account_ids))
        ).all()
        mapped: dict[int, dict[str, str]] = {}
        for row in rows:
            mapped.setdefault(row.account_id, {})[row.due_date.isoformat()] = row.status
        return mapped

    @classmethod
    def _to_read(
        cls,
        account: Account,
        bank: Bank,
        account_type: AccountType,
        coverages: dict[str, str] | None = None,
    ) -> AccountRead:
        type_name = account_type.name
        is_liability = type_name in LIABILITY_ACCOUNT_TYPES
        utilization = None
        if (
            is_liability
            and account.credit_limit is not None
            and account.credit_limit > 0
        ):
            utilization = round(account.current_balance / account.credit_limit, 4)

        labels = {name: label for name, label in ACCOUNT_TYPE_SEED}
        coverages = coverages or {}
        scheduled: list[ScheduledPayment] = []
        if is_liability:
            amount = (
                account.minimum_payment
                if account.minimum_payment is not None
                else account.current_balance
            )
            for due in upcoming_payment_dates(
                frequency=account.payment_frequency,
                anchor=account.recurrence_anchor,
                due_date_day=account.due_date_day,
                today=date.today(),
                end_date=account.recurrence_end,
                remaining_payments=account.remaining_payments,
                include_overdue=True,
            ):
                key = due.isoformat()
                scheduled.append(
                    ScheduledPayment(
                        date=key,
                        amount=amount,
                        coverage=coverages.get(key),
                    )
                )

        next_due = next((item.date for item in scheduled if item.coverage not in VALID_COVERAGE), None)
        frequency = account.payment_frequency
        return AccountRead(
            id=account.id,  # type: ignore[arg-type]
            name=account.name,
            bank_id=account.bank_id,
            bank_name=bank.name,
            bank_display_name=bank_display_name(bank.name),
            account_type_id=account.account_type_id,
            account_type=type_name,
            account_type_label=account_type.description or labels.get(type_name, type_name),
            is_liability=is_liability,
            current_balance=account.current_balance,
            currency=account.currency,
            last_four=account.last_four,
            credit_limit=account.credit_limit,
            utilization=utilization,
            apr=account.apr,
            minimum_payment=account.minimum_payment,
            due_date_day=account.due_date_day,
            cutoff_date_day=account.cutoff_date_day,
            next_due_date=next_due,
            payment_frequency=frequency,
            payment_frequency_label=PAYMENT_FREQUENCY_LABELS.get(frequency) if frequency else None,
            recurrence_anchor=account.recurrence_anchor,
            recurrence_end=account.recurrence_end,
            remaining_payments=account.remaining_payments,
            scheduled_payments=scheduled,
            is_active=account.is_active,
            last_snapshot_at=account.last_snapshot_at,
            has_statement_password=bool(account.statement_password),
            account_number=account.account_number,
        )
