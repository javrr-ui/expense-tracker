"""CRUD and spending stats for categories."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import col, select

from database.database import Database
from models.category import Category, CategoryCreate, CategoryRead, SubcategoryCreate, SubcategoryRead
from models.subcategory import Subcategory
from models.transaction import Transaction

logger = logging.getLogger("expense_tracker")


class CategoryService:
    def __init__(self, db: Database):
        self.db = db

    def list_tree(self) -> list[CategoryRead]:
        with self.db.session() as session:
            categories = session.exec(select(Category).order_by(col(Category.name))).all()
            subs = session.exec(select(Subcategory).order_by(col(Subcategory.name))).all()
            by_cat: dict[int, list[SubcategoryRead]] = {}
            for sub in subs:
                if sub.id is None:
                    continue
                by_cat.setdefault(sub.category_id, []).append(
                    SubcategoryRead(
                        id=sub.id,
                        name=sub.name,
                        category_id=sub.category_id,
                        description=sub.description,
                    )
                )
            result = []
            for category in categories:
                if category.id is None:
                    continue
                result.append(
                    CategoryRead(
                        id=category.id,
                        name=category.name,
                        description=category.description,
                        color=category.color,
                        kind=category.kind,
                        subcategories=by_cat.get(category.id, []),
                    )
                )
            return result

    def create_category(self, data: CategoryCreate) -> CategoryRead:
        with self.db.session() as session:
            category = Category(
                name=data.name.strip(),
                description=data.description,
                color=data.color,
                kind=data.kind,
            )
            session.add(category)
            try:
                session.flush()
            except IntegrityError as exc:
                raise ValueError("Ya existe una categoría con ese nombre") from exc
            return CategoryRead(
                id=category.id,  # type: ignore[arg-type]
                name=category.name,
                description=category.description,
                color=category.color,
                kind=category.kind,
                subcategories=[],
            )

    def create_subcategory(self, category_id: int, data: SubcategoryCreate) -> SubcategoryRead:
        with self.db.session() as session:
            category = session.get(Category, category_id)
            if category is None:
                raise LookupError("Category not found")
            sub = Subcategory(
                name=data.name.strip(),
                category_id=category_id,
                description=data.description,
            )
            session.add(sub)
            try:
                session.flush()
            except IntegrityError as exc:
                raise ValueError("Ya existe una subcategoría con ese nombre") from exc
            return SubcategoryRead(
                id=sub.id,  # type: ignore[arg-type]
                name=sub.name,
                category_id=category_id,
                description=sub.description,
            )

    def spending_by_category(
        self,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        tx_type: str = "expense",
    ) -> dict[str, Any]:
        with self.db.session() as session:
            stmt = select(Transaction, Category, Subcategory).outerjoin(
                Category, col(Category.id) == col(Transaction.category_id)
            ).outerjoin(
                Subcategory, col(Subcategory.id) == col(Transaction.subcategory_id)
            )
            if tx_type:
                stmt = stmt.where(Transaction.type == tx_type)
            if date_from is not None:
                stmt = stmt.where(col(Transaction.date) >= date_from)
            if date_to is not None:
                stmt = stmt.where(col(Transaction.date) <= date_to)

            rows = session.exec(stmt).all()
            buckets: dict[str, dict[str, Any]] = {}
            uncategorized = 0.0
            total = 0.0
            for tx, category, subcategory in rows:
                if getattr(tx, "excluded_from_budget", False):
                    continue
                if getattr(tx, "kind", None) in {"payment", "transfer"}:
                    continue
                currency = (getattr(tx, "currency", None) or "MXN").upper()
                if currency != "MXN":
                    amount = float(getattr(tx, "amount_mxn", None) or 0)
                    if amount <= 0:
                        continue
                else:
                    amount = float(tx.amount or 0)
                total += amount
                if category is None:
                    uncategorized += amount
                    key = "__none__"
                    bucket = buckets.setdefault(
                        key,
                        {
                            "category_id": None,
                            "category_name": "Sin categoría",
                            "color": "#9ca3af",
                            "kind": "expense",
                            "amount": 0.0,
                            "subs": {},
                        },
                    )
                else:
                    key = str(category.id)
                    bucket = buckets.setdefault(
                        key,
                        {
                            "category_id": category.id,
                            "category_name": category.name,
                            "color": category.color,
                            "kind": category.kind,
                            "amount": 0.0,
                            "subs": {},
                        },
                    )
                bucket["amount"] += amount
                sub_name = subcategory.name if subcategory is not None else "Sin subcategoría"
                sub_id = subcategory.id if subcategory is not None else None
                sub_key = str(sub_id) if sub_id is not None else "none"
                sub_bucket = bucket["subs"].setdefault(
                    sub_key,
                    {"subcategory_id": sub_id, "subcategory_name": sub_name, "amount": 0.0},
                )
                sub_bucket["amount"] += amount

            categories = []
            for bucket in buckets.values():
                amount = round(bucket["amount"], 2)
                categories.append(
                    {
                        "category_id": bucket["category_id"],
                        "category_name": bucket["category_name"],
                        "color": bucket["color"],
                        "kind": bucket["kind"],
                        "amount": amount,
                        "pct": round(amount / total, 4) if total else 0,
                        "subcategories": sorted(
                            (
                                {
                                    "subcategory_id": item["subcategory_id"],
                                    "subcategory_name": item["subcategory_name"],
                                    "amount": round(item["amount"], 2),
                                }
                                for item in bucket["subs"].values()
                            ),
                            key=lambda item: item["amount"],
                            reverse=True,
                        ),
                    }
                )
            categories.sort(key=lambda item: item["amount"], reverse=True)
            return {
                "total": round(total, 2),
                "uncategorized": round(uncategorized, 2),
                "categories": categories,
            }
