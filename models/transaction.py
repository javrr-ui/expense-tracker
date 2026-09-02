"""Transaction data model.

This module defines the Transaction Pydantic model used throughout the expense tracker
to represent a single financial transaction parsed from bank notification emails.

The model includes core fields required for storage and display, optional categorization
fields for future use, and a custom __str__ method for human-readable formatting.
"""

from datetime import datetime
from typing import Literal, Optional
from sqlmodel import Field, SQLModel
from pydantic import BaseModel


class TransactionCategoryUpdate(BaseModel):
    """Manual category assignment."""

    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    """Partial update for notes, tags, kind, account, and category."""

    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    kind: Optional[str] = None
    account_id: Optional[int] = None
    excluded_from_budget: Optional[bool] = None
    reimbursable: Optional[bool] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[datetime] = None
    merchant: Optional[str] = None


class TransactionCreate(BaseModel):
    """Data model for creating a new transaction."""

    email_id: str = ""
    date: Optional[datetime] = None
    amount: float
    description: str = ""
    type: Literal["expense", "income"]
    bank_name: str
    merchant: Optional[str] = None
    reference: Optional[str] = None
    status: str = "approved"
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    kind: Optional[str] = None
    account_id: Optional[int] = None
    source: str = "email"
    excluded_from_budget: bool = False
    reimbursable: bool = False
    currency: str = "MXN"
    amount_mxn: Optional[float] = None


class Transaction(SQLModel, table=True):
    """
    Represents a single financial transaction extracted from a bank email notification.

    This model is used both for parsing incoming emails and for storing transactions
    in the SQLite database.

    Attributes:
        date: Date and time of the transaction (may be None if not parsed)
        email_id: Unique Gmail message ID used for deduplication
        source: Bank/institution that sent the notification
        amount: Transaction amount (positive value; type determines income/expense)
        description: Human-readable description of the transaction
        type: "expense" for outflows, "income" for inflows
        category_name: Optional main category (e.g., "Food", "Transport") - currently unused
        subcategory_name: Optional subcategory - currently unused
        merchant: Name of the merchant/store (when available)
        reference: Transaction reference number (when available)
        status: Transaction status - defaults to "approved"
    """

    __tablename__ = "transactions"  # type: ignore

    transaction_id: int | None = Field(default=None, primary_key=True)
    date: datetime | None
    email_id: str = Field(unique=True)
    bank_id: int = Field(foreign_key="bank.id")
    amount: float
    description: str
    type: str
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    subcategory_id: Optional[int] = Field(default=None, foreign_key="subcategory.id")
    category_source: str | None = Field(default=None, max_length=16)
    category_locked: bool = Field(default=False)
    merchant: str | None = None
    reference: str | None = None
    notes: str | None = None
    tags: str | None = None
    kind: str | None = Field(default=None, max_length=16)
    account_id: int | None = Field(default=None, foreign_key="accounts.id")
    source: str = Field(default="email", max_length=16)
    balance_applied: bool = Field(default=False)
    excluded_from_budget: bool = Field(default=False)
    reimbursable: bool = Field(default=False)
    currency: str = Field(default="MXN", max_length=3)
    amount_mxn: float | None = Field(default=None)

    def __str__(self) -> str:
        date_str = self.date.strftime("%Y-%m-%d %H:%M:%S") if self.date else "None"
        amount_str = f"${self.amount:,.2f}"

        return (
            f"  Banco      : {self.bank_id}\n"
            f"  Transacción: {self.description}\n"
            f"  Fecha      : {date_str}\n"
            f"  Monto      : {amount_str}\n"
            f"  Tipo       : {self.type}\n"
            f"  Comercio   : {self.merchant or 'N/A'}\n"
            f"  Referencia : {self.reference or 'N/A'}\n"
        )
