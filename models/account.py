"""Account model and API schemas.

Account is the unit of money: a credit card, loan, checking account, or wallet.
`current_balance` is a snapshot-based running total (see BalanceSnapshot).
"""

from datetime import date, datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from sqlmodel import Field as SQLField, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Account(SQLModel, table=True):
    """Represents a financial account (card, loan, checking, or wallet)."""

    __tablename__ = "accounts"  # type: ignore

    id: int | None = SQLField(default=None, primary_key=True)
    bank_id: int = SQLField(foreign_key="bank.id")
    name: str = SQLField(index=True, unique=True)
    account_number: str | None = SQLField(default=None, unique=True)
    account_type_id: int = SQLField(foreign_key="account_type.id")
    current_balance: float = SQLField(default=0.0)
    currency: str = SQLField(default="MXN", max_length=3)
    apr: float = SQLField(default=0.0, description="Annual Percentage Rate")
    minimum_payment: float | None = SQLField(default=None)
    due_date_day: int | None = SQLField(
        default=None, description="Day of the month when payment is due"
    )
    cutoff_date_day: int | None = SQLField(
        default=None, description="Day of the month when billing cycle cuts off"
    )
    last_four: str | None = SQLField(default=None, max_length=4)
    credit_limit: float | None = SQLField(default=None)
    is_active: bool = SQLField(default=True)
    last_snapshot_at: datetime | None = SQLField(default=None)
    statement_password: str | None = SQLField(default=None)
    payment_frequency: str | None = SQLField(default=None, max_length=16)
    recurrence_anchor: date | None = SQLField(default=None)
    recurrence_end: date | None = SQLField(default=None)
    remaining_payments: int | None = SQLField(default=None)
    created_at: datetime = SQLField(default_factory=utc_now)
    updated_at: datetime = SQLField(default_factory=utc_now)


def _empty_to_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_frequency(value: Optional[str]) -> Optional[str]:
    from constants.payment_frequency import VALID_FREQUENCIES

    value = _empty_to_none(value) if isinstance(value, str) else value
    if value is None:
        return None
    if value not in VALID_FREQUENCIES:
        raise ValueError("Frecuencia inválida. Usa weekly, biweekly o monthly.")
    return value


class AccountCreate(BaseModel):
    """Payload for creating an account. Optional opening balance becomes the first snapshot."""

    name: str = Field(min_length=1, max_length=120)
    bank_name: str = Field(min_length=1, max_length=80)
    account_type: str
    account_number: Optional[str] = None
    last_four: Optional[str] = None
    credit_limit: Optional[float] = Field(default=None, ge=0)
    current_balance: float = 0.0
    currency: str = Field(default="MXN", min_length=3, max_length=3)
    apr: float = Field(default=0.0, ge=0)
    minimum_payment: Optional[float] = Field(default=None, ge=0)
    due_date_day: Optional[int] = Field(default=None, ge=1, le=31)
    cutoff_date_day: Optional[int] = Field(default=None, ge=1, le=31)
    statement_password: Optional[str] = None
    payment_frequency: Optional[str] = None
    recurrence_anchor: Optional[date] = None
    recurrence_end: Optional[date] = None
    remaining_payments: Optional[int] = Field(default=None, ge=1, le=600)

    @field_validator("name", "bank_name", "account_type", "currency", mode="before")
    @classmethod
    def strip_required(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @field_validator("account_number", "statement_password", mode="before")
    @classmethod
    def strip_optional(cls, value: Optional[str]) -> Optional[str]:
        return _empty_to_none(value)

    @field_validator("last_four")
    @classmethod
    def validate_last_four(cls, value: Optional[str]) -> Optional[str]:
        value = _empty_to_none(value)
        if value is None:
            return None
        if not value.isdigit() or len(value) != 4:
            raise ValueError("last_four must be exactly 4 digits")
        return value

    @field_validator("payment_frequency", mode="before")
    @classmethod
    def validate_frequency(cls, value: Optional[str]) -> Optional[str]:
        return _parse_frequency(value)


class AccountUpdate(BaseModel):
    """Partial update. Balance changes go through POST /accounts/{id}/balance."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    bank_name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    account_type: Optional[str] = None
    account_number: Optional[str] = None
    last_four: Optional[str] = None
    credit_limit: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    apr: Optional[float] = Field(default=None, ge=0)
    minimum_payment: Optional[float] = Field(default=None, ge=0)
    due_date_day: Optional[int] = Field(default=None, ge=1, le=31)
    cutoff_date_day: Optional[int] = Field(default=None, ge=1, le=31)
    is_active: Optional[bool] = None
    statement_password: Optional[str] = None
    payment_frequency: Optional[str] = None
    recurrence_anchor: Optional[date] = None
    recurrence_end: Optional[date] = None
    remaining_payments: Optional[int] = Field(default=None, ge=1, le=600)

    @field_validator("name", "bank_name", "account_type", "currency", mode="before")
    @classmethod
    def strip_optional_required(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip()

    @field_validator("account_number", "statement_password", mode="before")
    @classmethod
    def strip_optional(cls, value: Optional[str]) -> Optional[str]:
        return _empty_to_none(value) if value is not None else None

    @field_validator("last_four")
    @classmethod
    def validate_last_four(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = _empty_to_none(value)
        if value is None:
            return None
        if not value.isdigit() or len(value) != 4:
            raise ValueError("last_four must be exactly 4 digits")
        return value

    @field_validator("payment_frequency", mode="before")
    @classmethod
    def validate_frequency(cls, value: Optional[str]) -> Optional[str]:
        return _parse_frequency(value)


class BalanceUpdate(BaseModel):
    """Manual balance snapshot."""

    amount: float
    as_of: Optional[datetime] = None
    note: Optional[str] = Field(default=None, max_length=500)


class BalanceSnapshotRead(BaseModel):
    """Serialized balance snapshot. Safe for web and mobile clients."""

    id: int
    amount: float
    as_of: datetime
    source: str
    note: Optional[str] = None


class ScheduledPayment(BaseModel):
    """One occurrence of a payment recurrence."""

    date: str
    amount: float
    coverage: str | None = None


class AccountRead(BaseModel):
    """Serialized account. Never includes statement_password."""

    id: int
    name: str
    bank_id: int
    bank_name: str
    bank_display_name: str
    account_type_id: int
    account_type: str
    account_type_label: str
    is_liability: bool
    current_balance: float
    currency: str
    last_four: Optional[str] = None
    credit_limit: Optional[float] = None
    utilization: Optional[float] = None
    apr: float
    minimum_payment: Optional[float] = None
    due_date_day: Optional[int] = None
    cutoff_date_day: Optional[int] = None
    next_due_date: Optional[str] = None
    payment_frequency: Optional[str] = None
    payment_frequency_label: Optional[str] = None
    recurrence_anchor: Optional[date] = None
    recurrence_end: Optional[date] = None
    remaining_payments: Optional[int] = None
    scheduled_payments: list[ScheduledPayment] = Field(default_factory=list)
    is_active: bool
    last_snapshot_at: Optional[datetime] = None
    has_statement_password: bool
    account_number: Optional[str] = None


class AccountDetail(AccountRead):
    """Account plus recent snapshots for the detail screen."""

    snapshots: list[BalanceSnapshotRead] = Field(default_factory=list)


class UpcomingPayment(BaseModel):
    """A future payment due, for the dashboard calendar list."""

    account_id: int
    account_name: str
    bank_display_name: str
    amount: float
    due_date: str
    status: str = "upcoming"


class DashboardRead(BaseModel):
    """Single payload for the home screen (web now, mobile later)."""

    total_debt: float
    total_assets: float
    net_position: float
    liability_accounts: list[AccountRead]
    asset_accounts: list[AccountRead]
    upcoming_payments: list[UpcomingPayment]


class AccountTypeRead(BaseModel):
    """Account type option for create/edit forms."""

    name: str
    label: str
    is_liability: bool


class BankOption(BaseModel):
    """Bank option for create/edit forms."""

    name: str
    display_name: str
