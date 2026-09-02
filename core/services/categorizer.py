"""Assign categories to transactions using keyword/merchant rules."""

from __future__ import annotations

from dataclasses import dataclass

from unidecode import unidecode
from sqlmodel import Session, col, select

from models.category import Category
from models.category_rule import CategoryRule
from models.subcategory import Subcategory
from models.transaction import Transaction


@dataclass(frozen=True)
class Classification:
    category_id: int
    subcategory_id: int | None
    source: str = "auto"


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return unidecode(value).lower().strip()


class Categorizer:
    """Match a transaction against stored rules. Higher priority wins."""

    def classify(self, session: Session, tx: Transaction) -> Classification | None:
        haystack = f"{normalize_text(tx.merchant)} {normalize_text(tx.description)}"
        merchant = normalize_text(tx.merchant)
        if not haystack.strip():
            return None

        rules = session.exec(
            select(CategoryRule).order_by(col(CategoryRule.priority).desc(), col(CategoryRule.id))
        ).all()
        for rule in rules:
            pattern = normalize_text(rule.pattern)
            if not pattern:
                continue
            if rule.match_type == "merchant":
                if merchant and merchant == pattern:
                    return Classification(rule.category_id, rule.subcategory_id)
            elif pattern in haystack:
                return Classification(rule.category_id, rule.subcategory_id)
        return None

    def apply_to_transaction(self, session: Session, tx: Transaction) -> bool:
        """Set category if the transaction is not locked. Returns True if changed."""
        if tx.category_locked:
            return False
        result = self.classify(session, tx)
        if result is None:
            return False
        changed = (
            tx.category_id != result.category_id
            or tx.subcategory_id != result.subcategory_id
        )
        tx.category_id = result.category_id
        tx.subcategory_id = result.subcategory_id
        tx.category_source = "auto"
        return changed

    def learn_from_assignment(
        self,
        session: Session,
        tx: Transaction,
        category_id: int,
        subcategory_id: int | None,
    ) -> None:
        """Create or boost a rule from a manual assignment."""
        merchant = normalize_text(tx.merchant)
        if merchant:
            match_type = "merchant"
            pattern = merchant
            priority = 500
        else:
            description = normalize_text(tx.description)
            if len(description) < 4:
                return
            match_type = "keyword"
            pattern = description[:80]
            priority = 450

        existing = session.exec(
            select(CategoryRule).where(
                CategoryRule.pattern == pattern,
                CategoryRule.match_type == match_type,
            )
        ).first()
        if existing:
            existing.category_id = category_id
            existing.subcategory_id = subcategory_id
            existing.priority = max(existing.priority, priority)
            existing.source = "learned"
            session.add(existing)
            return

        session.add(
            CategoryRule(
                pattern=pattern,
                match_type=match_type,
                category_id=category_id,
                subcategory_id=subcategory_id,
                priority=priority,
                source="learned",
            )
        )


def resolve_category_ids(
    session: Session, category_id: int | None, subcategory_id: int | None
) -> tuple[int | None, int | None]:
    if subcategory_id is not None:
        sub = session.get(Subcategory, subcategory_id)
        if sub is None:
            raise ValueError("Subcategoría no encontrada")
        if category_id is not None and sub.category_id != category_id:
            raise ValueError("La subcategoría no pertenece a esa categoría")
        return sub.category_id, sub.id
    if category_id is not None:
        category = session.get(Category, category_id)
        if category is None:
            raise ValueError("Categoría no encontrada")
        return category.id, None
    return None, None
