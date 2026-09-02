"""Category data model and API schemas."""

from typing import Optional

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, SQLModel


class Category(SQLModel, table=True):
    """Represents a transaction category."""

    __tablename__ = "category"  # type: ignore

    id: int | None = SQLField(default=None, primary_key=True)
    name: str = SQLField(index=True, unique=True)
    description: str | None = None
    color: str = SQLField(default="#6b7280", max_length=16)
    kind: str = SQLField(default="expense", max_length=16)


class SubcategoryRead(BaseModel):
    id: int
    name: str
    category_id: int
    description: Optional[str] = None


class CategoryRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    color: str
    kind: str
    subcategories: list[SubcategoryRead] = Field(default_factory=list)


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: Optional[str] = None
    color: str = Field(default="#6b7280", max_length=16)
    kind: str = Field(default="expense")


class SubcategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: Optional[str] = None
