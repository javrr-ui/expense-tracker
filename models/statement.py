"""Bank statement records."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    from datetime import timezone

    return datetime.now(timezone.utc).replace(tzinfo=None)


class Statement(SQLModel, table=True):
    __tablename__ = "statements"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    period_start: date | None = None
    period_end: date | None = None
    previous_balance: float | None = None
    closing_balance: float | None = None
    minimum_payment: float | None = None
    due_date: date | None = None
    source: str = Field(default="upload", max_length=16)
    email_id: str | None = None
    source_filename: str | None = None
    stored_path: str | None = None
    status: str = Field(default="uploaded", max_length=24)
    raw_text: str | None = None
    error: str | None = None
    parsed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class StatementRead(BaseModel):
    id: int
    account_id: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    previous_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    minimum_payment: Optional[float] = None
    due_date: Optional[date] = None
    source: str
    status: str
    source_filename: Optional[str] = None
    error: Optional[str] = None
    parsed_at: Optional[datetime] = None
