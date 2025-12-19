
from datetime import datetime
from pydantic import BaseModel

class Transaction(BaseModel):
    date: datetime
    amount: float
    description: str
    type: str
    merchant: str | None = None
    reference: str | None = None
    status: str = "approved"