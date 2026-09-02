"""Rules that map merchant/description text to a category."""

from sqlmodel import Field, SQLModel


class CategoryRule(SQLModel, table=True):
    """A pattern that assigns category/subcategory to a transaction."""

    __tablename__ = "category_rule"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    pattern: str = Field(index=True)
    match_type: str = Field(default="keyword", max_length=16)
    category_id: int = Field(foreign_key="category.id")
    subcategory_id: int | None = Field(default=None, foreign_key="subcategory.id")
    priority: int = Field(default=100)
    source: str = Field(default="seed", max_length=16)
