"""Monthly budgets vs actual spending."""

from __future__ import annotations

from calendar import monthrange
from datetime import datetime

from sqlmodel import col, select

from core.services.category_service import CategoryService
from database.database import Database
from models.budget import Budget, BudgetUpsert
from models.category import Category


class BudgetService:
    def __init__(self, db: Database):
        self.db = db

    def upsert(self, data: BudgetUpsert) -> dict:
        with self.db.session() as session:
            if session.get(Category, data.category_id) is None:
                raise LookupError("Category not found")
            existing = session.exec(
                select(Budget).where(
                    Budget.category_id == data.category_id,
                    Budget.year == data.year,
                    Budget.month == data.month,
                )
            ).first()
            if existing:
                existing.amount = data.amount
                existing.updated_at = datetime.now().replace(tzinfo=None)
                session.add(existing)
                budget = existing
            else:
                budget = Budget(
                    category_id=data.category_id,
                    year=data.year,
                    month=data.month,
                    amount=data.amount,
                )
                session.add(budget)
                session.flush()
            return {
                "id": budget.id,
                "category_id": budget.category_id,
                "year": budget.year,
                "month": budget.month,
                "amount": budget.amount,
            }

    def month_report(self, year: int, month: int) -> dict:
        last_day = monthrange(year, month)[1]
        start = datetime(year, month, 1)
        end = datetime(year, month, last_day, 23, 59, 59)
        stats = CategoryService(self.db).spending_by_category(date_from=start, date_to=end, tx_type="expense")
        with self.db.session() as session:
            budgets = [
                {
                    "category_id": row.category_id,
                    "amount": row.amount,
                }
                for row in session.exec(
                    select(Budget).where(Budget.year == year, Budget.month == month)
                ).all()
            ]
            categories = {
                row.id: {"name": row.name, "color": row.color}
                for row in session.exec(select(Category)).all()
            }
        spent_by_id = {
            item["category_id"]: item
            for item in stats["categories"]
            if item["category_id"] is not None
        }
        rows = []
        for budget in budgets:
            category = categories.get(budget["category_id"])
            actual = spent_by_id.get(budget["category_id"], {})
            spent = actual.get("amount", 0.0)
            rows.append(
                {
                    "category_id": budget["category_id"],
                    "category_name": category["name"] if category else "—",
                    "color": category["color"] if category else "#6b7280",
                    "budget": budget["amount"],
                    "spent": spent,
                    "remaining": round(budget["amount"] - spent, 2),
                    "pct": round(spent / budget["amount"], 4) if budget["amount"] else 0,
                }
            )
        for item in stats["categories"]:
            if item["category_id"] and item["category_id"] not in {row["category_id"] for row in rows}:
                rows.append(
                    {
                        "category_id": item["category_id"],
                        "category_name": item["category_name"],
                        "color": item["color"],
                        "budget": 0,
                        "spent": item["amount"],
                        "remaining": -item["amount"],
                        "pct": None,
                    }
                )
        return {"year": year, "month": month, "items": rows, "total_spent": stats["total"]}
