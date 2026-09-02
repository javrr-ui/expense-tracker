"""Monthly category budgets."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, SQLModel, UniqueConstraint


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Budget(SQLModel, table=True):
    __tablename__ = "budgets"  # type: ignore
    __table_args__ = (UniqueConstraint("category_id", "year", "month"),)

    id: int | None = SQLField(default=None, primary_key=True)
    category_id: int = SQLField(foreign_key="category.id", index=True)
    year: int
    month: int
    amount: float = SQLField(default=0.0)
    updated_at: datetime = SQLField(default_factory=utc_now)


class BudgetUpsert(BaseModel):
    category_id: int
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)
    amount: float = Field(ge=0)
