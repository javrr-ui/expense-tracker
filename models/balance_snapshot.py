"""Balance snapshot model.

A snapshot is the source of truth for an account's balance at a point in time.
Later transactions only adjust the running balance if they occur after `as_of`.
"""

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BalanceSnapshot(SQLModel, table=True):
    """Recorded balance for an account at a given moment."""

    __tablename__ = "balance_snapshots"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    amount: float
    as_of: datetime
    source: str = Field(max_length=32)
    note: str | None = None
    statement_id: int | None = None
    created_at: datetime = Field(default_factory=utc_now)
