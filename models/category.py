"""Category data model."""

from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    """Represents a transaction category"""

    __tablename__ = "category" # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str | None = None
