"""Account model"""

from datetime import datetime
from sqlmodel import Field, SQLModel


class Account(SQLModel, table=True):
    """Represents a financial account"""

    __tablename__ = "accounts"  # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    bank_id: int = Field(foreign_key="bank.id")
    name: str = Field(index=True, unique=True)
    account_number: str | None = Field(default=None, unique=True)
    account_type_id: int = Field(foreign_key="account_type.id")
    current_balance: float = Field(default=0.0)
    currency: str = Field(default="MXN", max_length=3)
    apr: float = Field(
        default=0.0, description="Annual Percentage Rate"
    )
    minimum_payment: float | None = Field(default=None)
    due_date_day: int | None = Field(
        default=None, description="Day of the month when payment is due"
    )
    cutoff_date_day: int | None = Field(
        default=None, description="Day of the month when billing cycle cuts off"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
