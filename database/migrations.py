"""Additive SQLite migrations.

`SQLModel.metadata.create_all` creates missing tables but does not add columns
to tables that already exist. This module applies the extra ALTERs needed for
the accounts dashboard without requiring Alembic.
"""

import logging

from sqlalchemy import inspect, text
from sqlmodel import Session, select

from constants.account_types import ACCOUNT_TYPE_SEED
from constants.categories import CATEGORY_SEED, RULE_SEED, SUBCATEGORY_SEED
from models.account_type import AccountType
from models.category import Category
from models.category_rule import CategoryRule
from models.subcategory import Subcategory

logger = logging.getLogger("expense_tracker")

ACCOUNT_COLUMNS = {
    "last_four": "VARCHAR(4)",
    "credit_limit": "FLOAT",
    "is_active": "BOOLEAN DEFAULT 1",
    "last_snapshot_at": "DATETIME",
    "statement_password": "VARCHAR",
    "payment_frequency": "VARCHAR(16)",
    "recurrence_anchor": "DATE",
    "recurrence_end": "DATE",
    "remaining_payments": "INTEGER",
}


TRANSACTION_COLUMNS = {
    "category_source": "VARCHAR(16)",
    "category_locked": "BOOLEAN DEFAULT 0",
    "notes": "TEXT",
    "tags": "TEXT",
    "kind": "VARCHAR(16)",
    "account_id": "INTEGER",
    "source": "VARCHAR(16) DEFAULT 'email'",
    "balance_applied": "BOOLEAN DEFAULT 0",
    "excluded_from_budget": "BOOLEAN DEFAULT 0",
    "reimbursable": "BOOLEAN DEFAULT 0",
    "currency": "VARCHAR(3) DEFAULT 'MXN'",
    "amount_mxn": "FLOAT",
}

CATEGORY_COLUMNS = {
    "color": "VARCHAR(16) DEFAULT '#6b7280'",
    "kind": "VARCHAR(16) DEFAULT 'expense'",
}

SNAPSHOT_COLUMNS = {
    "statement_id": "INTEGER",
}


def run_migrations(engine) -> None:
    """Add any missing columns and seed reference data."""
    _ensure_account_columns(engine)
    _ensure_columns(engine, "transactions", TRANSACTION_COLUMNS)
    _ensure_columns(engine, "category", CATEGORY_COLUMNS)
    _ensure_columns(engine, "balance_snapshots", SNAPSHOT_COLUMNS)
    _seed_account_types(engine)
    _seed_categories(engine)


def _ensure_account_columns(engine) -> None:
    _ensure_columns(engine, "accounts", ACCOUNT_COLUMNS)


def _ensure_columns(engine, table: str, columns: dict[str, str]) -> None:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns(table)}
    with engine.begin() as conn:
        for name, ddl_type in columns.items():
            if name in existing:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl_type}"))
            logger.info("Added column %s.%s", table, name)


def _seed_account_types(engine) -> None:
    with Session(engine) as session:
        existing = {row.name for row in session.exec(select(AccountType)).all()}
        created = False
        for name, description in ACCOUNT_TYPE_SEED:
            if name in existing:
                continue
            session.add(AccountType(name=name, description=description))
            created = True
        if created:
            session.commit()
            logger.info("Seeded account types")


def _seed_categories(engine) -> None:
    from core.services.categorizer import normalize_text

    with Session(engine) as session:
        existing = {row.name: row for row in session.exec(select(Category)).all()}
        created = False
        for name, color, kind, description in CATEGORY_SEED:
            if name in existing:
                category = existing[name]
                if not category.color:
                    category.color = color
                if not category.kind:
                    category.kind = kind
                session.add(category)
                continue
            category = Category(name=name, color=color, kind=kind, description=description)
            session.add(category)
            session.flush()
            existing[name] = category
            created = True

        existing_subs = {row.name: row for row in session.exec(select(Subcategory)).all()}
        for sub_name, category_name in SUBCATEGORY_SEED:
            if sub_name in existing_subs:
                continue
            category = existing.get(category_name)
            if category is None or category.id is None:
                continue
            session.add(Subcategory(name=sub_name, category_id=category.id))
            created = True
        session.flush()
        existing_subs = {row.name: row for row in session.exec(select(Subcategory)).all()}

        existing_rules = {
            (row.pattern, row.match_type, row.source)
            for row in session.exec(select(CategoryRule)).all()
        }
        for pattern, match_type, category_name, sub_name, priority in RULE_SEED:
            normalized = normalize_text(pattern)
            key = (normalized, match_type, "seed")
            if key in existing_rules:
                continue
            category = existing.get(category_name)
            sub = existing_subs.get(sub_name)
            if category is None or category.id is None:
                continue
            session.add(
                CategoryRule(
                    pattern=normalized,
                    match_type=match_type,
                    category_id=category.id,
                    subcategory_id=sub.id if sub is not None else None,
                    priority=priority,
                    source="seed",
                )
            )
            created = True
        if created:
            session.commit()
            logger.info("Seeded categories and rules")
        else:
            session.commit()
