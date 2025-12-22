
from datetime import datetime
from pydantic import BaseModel

from constants.banks import SupportedBanks

class Transaction(BaseModel):
    date: datetime | None
    bank_name: SupportedBanks
    amount: float
    description: str
    type: str
    merchant: str | None = None
    reference: str | None = None
    status: str = "approved"
    
    def __str__(self) -> str:
            date_str = self.date.strftime("%Y-%m-%d %H:%M:%S") if self.date else "None"
            amount_str = f"${self.amount:,.2f}"
            # Formato con separador de miles y 2 decimales (ajustado a español si quieres)
            
            return (
                f"  Banco      : {self.bank_name}\n"
                f"  Transacción: {self.description}\n"
                f"  Fecha      : {date_str}\n"
                f"  Monto      : {amount_str}\n"
                f"  Tipo       : {self.type}\n"
                f"  Comercio   : {self.merchant or 'N/A'}\n"
                f"  Referencia : {self.reference or 'N/A'}\n"
                f"  Estado     : {self.status}"
            )