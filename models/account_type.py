"""Account type model"""

from sqlmodel import Field, SQLModel

class AccountType(SQLModel, table=True):
    """Represents an account type"""

    __tablename__ = "account_type" # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str | None = Field(default=None)
