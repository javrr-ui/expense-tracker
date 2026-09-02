"""Manual coverage of a generated payment due date."""

from datetime import date, datetime, timezone

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, SQLModel, UniqueConstraint

VALID_COVERAGE = frozenset({"minimum_paid", "paid_in_full"})


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PaymentCoverage(SQLModel, table=True):
    __tablename__ = "payment_coverages"  # type: ignore
    __table_args__ = (UniqueConstraint("account_id", "due_date"),)

    id: int | None = SQLField(default=None, primary_key=True)
    account_id: int = SQLField(foreign_key="accounts.id", index=True)
    due_date: date
    status: str = SQLField(max_length=24)
    note: str | None = None
    updated_at: datetime = SQLField(default_factory=utc_now)


class PaymentCoverageUpsert(BaseModel):
    due_date: date
    status: str | None = Field(
        default="minimum_paid",
        description="minimum_paid, paid_in_full, or null to clear",
    )
    note: str | None = None
