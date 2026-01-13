"""Bank data model."""

from sqlmodel import SQLModel, Field


class Bank(SQLModel, table=True):
    """Represents a bank entity in the expense tracking system."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
