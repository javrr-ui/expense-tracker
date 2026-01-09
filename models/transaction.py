"""Transaction data model.

This module defines the Transaction Pydantic model used throughout the expense tracker
to represent a single financial transaction parsed from bank notification emails.

The model includes core fields required for storage and display, optional categorization
fields for future use, and a custom __str__ method for human-readable formatting.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from constants.banks import SupportedBanks


class Transaction(BaseModel):
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

    date: datetime | None
    email_id: str
    source: SupportedBanks
    amount: float
    description: str
    type: Literal["expense", "income"]
    category_name: str = ""
    subcategory_name: str = ""
    merchant: str | None = None
    reference: str | None = None
    status: str = "approved"

    def __str__(self) -> str:
        date_str = self.date.strftime("%Y-%m-%d %H:%M:%S") if self.date else "None"
        amount_str = f"${self.amount:,.2f}"
        # Formato con separador de miles y 2 decimales (ajustado a español si quieres)

        return (
            f"  Banco      : {self.source}\n"
            f"  Transacción: {self.description}\n"
            f"  Fecha      : {date_str}\n"
            f"  Monto      : {amount_str}\n"
            f"  Tipo       : {self.type}\n"
            f"  Comercio   : {self.merchant or 'N/A'}\n"
            f"  Referencia : {self.reference or 'N/A'}\n"
            f"  Estado     : {self.status}"
        )
