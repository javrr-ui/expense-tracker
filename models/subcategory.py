"""Subcategory data model."""

from sqlmodel import Field, SQLModel


class Subcategory(SQLModel, table=True):
    """Represents a transaction subcategory"""

    __tablename__ = "subcategory"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    category_id: int = Field(foreign_key="category.id")
    description: str | None = None
