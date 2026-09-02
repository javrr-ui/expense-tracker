"""Transaction service for managing transactions."""

from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import logging
import uuid
from sqlmodel import col, desc, func, select
from sqlalchemy.exc import SQLAlchemyError

from core.services.account_resolver import resolve_account
from core.services.balance_delta import apply_if_needed, reverse_if_applied
from core.services.categorizer import Categorizer, resolve_category_ids
from core.services.transaction_kind import VALID_KINDS, infer_kind
from database.database import Database
from models.account import Account
from models.bank import Bank
from models.category import Category
from models.subcategory import Subcategory
from models.transaction import Transaction, TransactionCategoryUpdate, TransactionCreate, TransactionUpdate


logger = logging.getLogger("expense_tracker")


class TransactionService:
    """Service for managing transactions in the database."""

    def __init__(self, db: Database):
        """Initialize with a Database instance."""
        self.db = db
        self.categorizer = Categorizer()

    def save_transaction(self, transaction: TransactionCreate) -> Optional[int]:
        """Save a transaction to the database. Skips duplicates by email_id."""
        with self.db.session() as session:
            try:
                email_id = transaction.email_id.strip() if transaction.email_id else ""
                if not email_id:
                    email_id = f"manual:{uuid.uuid4()}"
                elif session.exec(
                    select(Transaction).where(Transaction.email_id == email_id)
                ).first():
                    logger.info("Duplicate email_id skipped: %s", email_id)
                    return None

                stmt = select(Bank).where(Bank.name == transaction.bank_name)
                bank = session.exec(stmt).first()

                if bank is None:
                    bank = Bank(name=transaction.bank_name)
                    session.add(bank)
                    session.commit()
                    session.refresh(bank)

                if bank.id is None:
                    logger.error("Bank has no id after save: %s", transaction.bank_name)
                    return None

                tx = Transaction(
                    bank_id=bank.id,
                    email_id=email_id,
                    date=transaction.date,
                    amount=transaction.amount,
                    category_id=None,
                    subcategory_id=None,
                    description=transaction.description,
                    type=transaction.type,
                    merchant=transaction.merchant,
                    reference=transaction.reference,
                    notes=transaction.notes,
                    source=transaction.source or "email",
                    excluded_from_budget=transaction.excluded_from_budget,
                    reimbursable=transaction.reimbursable,
                    account_id=transaction.account_id,
                    kind=transaction.kind,
                    currency=(transaction.currency or "MXN").upper(),
                    amount_mxn=transaction.amount_mxn,
                )
                if transaction.tags:
                    tx.tags = json.dumps(_clean_tags(transaction.tags), ensure_ascii=False)

                session.add(tx)
                session.flush()
                tx.kind = infer_kind(tx)
                self.categorizer.apply_to_transaction(session, tx)
                if tx.account_id is None:
                    matched = resolve_account(session, tx)
                    if matched is not None:
                        tx.account_id = matched.id
                apply_if_needed(session, tx)
                session.commit()
                session.refresh(tx)

                logger.info(
                    "Transaction added [ID: %s] | %s | %s | %s | Category: %s | Subcategory: %s",
                    tx.transaction_id,
                    tx.amount,
                    tx.date,
                    tx.description,
                    tx.category_id,
                    tx.subcategory_id,
                )
                return tx.transaction_id
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(
                    "SQLAlchemy database error during save: %s", e, exc_info=True
                )
                return None

            except ValueError as e:
                session.rollback()
                logger.error("Value error (likely invalid data type): %s", e)
                return None

    def delete_transaction(self, transaction_id: int) -> None:
        with self.db.session() as session:
            tx = session.get(Transaction, transaction_id)
            if tx is None:
                raise LookupError("Transaction not found")
            reverse_if_applied(session, tx)
            session.delete(tx)

    def list_transactions(
        self,
        limit: int = 100,
        offset: int = 0,
        uncategorized: bool = False,
        unassigned: bool = False,
        account_id: int | None = None,
        kind: str | None = None,
        search: str | None = None,
        tag: str | None = None,
        reimbursable: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> List[Dict[str, Any]]:
        """List transactions with bank and category names."""
        with self.db.session() as session:
            try:
                stmt = self._join_stmt()
                stmt = self._apply_filters(
                    stmt,
                    uncategorized=uncategorized,
                    unassigned=unassigned,
                    account_id=account_id,
                    kind=kind,
                    search=search,
                    tag=tag,
                    reimbursable=reimbursable,
                    date_from=date_from,
                    date_to=date_to,
                )
                stmt = (
                    stmt.order_by(
                        desc(col(Transaction.date)),
                        desc(col(Transaction.transaction_id)),
                    )
                    .offset(offset)
                    .limit(limit)
                )
                results = session.exec(stmt).all()
                return [
                    self._map_transaction(tx, bank, category, subcategory, account)
                    for tx, bank, category, subcategory, account in results
                ]
            except SQLAlchemyError as e:
                logger.error("SQLAlchemy database error during list: %s", e, exc_info=True)
                return []

    def count_transactions(
        self,
        uncategorized: bool = False,
        unassigned: bool = False,
        account_id: int | None = None,
        kind: str | None = None,
        search: str | None = None,
        tag: str | None = None,
        reimbursable: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        """Return the total number of transactions."""
        with self.db.session() as session:
            try:
                stmt = select(func.count()).select_from(Transaction)  # pylint: disable=not-callable
                stmt = self._apply_filters(
                    stmt,
                    uncategorized=uncategorized,
                    unassigned=unassigned,
                    account_id=account_id,
                    kind=kind,
                    search=search,
                    tag=tag,
                    reimbursable=reimbursable,
                    date_from=date_from,
                    date_to=date_to,
                )
                return session.exec(stmt).one()
            except SQLAlchemyError as e:
                logger.error("SQLAlchemy database error during count: %s", e, exc_info=True)
                return 0

    def get_transaction(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """Get a single transaction by id."""
        with self.db.session() as session:
            try:
                stmt = self._join_stmt().where(Transaction.transaction_id == transaction_id)
                result = session.exec(stmt).first()
                if result is None:
                    return None
                tx, bank, category, subcategory, account = result
                return self._map_transaction(tx, bank, category, subcategory, account)
            except SQLAlchemyError as e:
                logger.error("SQLAlchemy database error during get: %s", e, exc_info=True)
                return None

    def assign_category(
        self, transaction_id: int, data: TransactionCategoryUpdate
    ) -> Dict[str, Any]:
        """Manually set category, lock it, and learn a rule."""
        with self.db.session() as session:
            tx = session.get(Transaction, transaction_id)
            if tx is None:
                raise LookupError("Transaction not found")
            category_id, subcategory_id = resolve_category_ids(
                session, data.category_id, data.subcategory_id
            )
            tx.category_id = category_id
            tx.subcategory_id = subcategory_id
            tx.category_source = "manual"
            tx.category_locked = True
            if category_id is not None:
                self.categorizer.learn_from_assignment(
                    session, tx, category_id, subcategory_id
                )
            session.add(tx)
            session.flush()
            stmt = self._join_stmt().where(Transaction.transaction_id == transaction_id)
            result = session.exec(stmt).one()
            mapped_tx, bank, category, subcategory, account = result
            return self._map_transaction(mapped_tx, bank, category, subcategory, account)

    def update_transaction(self, transaction_id: int, data: TransactionUpdate) -> Dict[str, Any]:
        """Update notes, tags, kind, account, and optionally category."""
        payload = data.model_dump(exclude_unset=True)
        with self.db.session() as session:
            tx = session.get(Transaction, transaction_id)
            if tx is None:
                raise LookupError("Transaction not found")

            if "category_id" in payload or "subcategory_id" in payload:
                category_id, subcategory_id = resolve_category_ids(
                    session,
                    payload.get("category_id", tx.category_id),
                    payload.get("subcategory_id", tx.subcategory_id),
                )
                tx.category_id = category_id
                tx.subcategory_id = subcategory_id
                tx.category_source = "manual"
                tx.category_locked = True
                if category_id is not None:
                    self.categorizer.learn_from_assignment(
                        session, tx, category_id, subcategory_id
                    )
                payload.pop("category_id", None)
                payload.pop("subcategory_id", None)

            if "tags" in payload:
                tags = payload.pop("tags")
                tx.tags = json.dumps(_clean_tags(tags), ensure_ascii=False) if tags else None

            if "notes" in payload:
                notes = payload.pop("notes")
                tx.notes = notes.strip() if isinstance(notes, str) and notes.strip() else None

            if "kind" in payload:
                kind = payload.pop("kind")
                if kind is not None and kind not in VALID_KINDS:
                    raise ValueError("Tipo de movimiento inválido")
                tx.kind = kind

            if "account_id" in payload:
                account_id = payload.pop("account_id")
                if account_id is not None and session.get(Account, account_id) is None:
                    raise ValueError("Cuenta no encontrada")
                if account_id != tx.account_id:
                    reverse_if_applied(session, tx)
                    tx.account_id = account_id

            if "excluded_from_budget" in payload:
                tx.excluded_from_budget = bool(payload.pop("excluded_from_budget"))
            if "reimbursable" in payload:
                tx.reimbursable = bool(payload.pop("reimbursable"))
            if "description" in payload and payload["description"] is not None:
                tx.description = payload.pop("description")
            if "amount" in payload and payload["amount"] is not None:
                reverse_if_applied(session, tx)
                tx.amount = payload.pop("amount")
            if "date" in payload:
                tx.date = payload.pop("date")
            if "merchant" in payload:
                tx.merchant = payload.pop("merchant")

            apply_if_needed(session, tx)
            session.add(tx)
            session.flush()
            stmt = self._join_stmt().where(Transaction.transaction_id == transaction_id)
            result = session.exec(stmt).one()
            mapped_tx, bank, category, subcategory, account = result
            return self._map_transaction(mapped_tx, bank, category, subcategory, account)

    def recategorize(self) -> Dict[str, int]:
        """Apply rules to unlocked transactions and fill missing kind."""
        updated = 0
        skipped_locked = 0
        kinds_filled = 0
        with self.db.session() as session:
            txs = session.exec(select(Transaction)).all()
            for tx in txs:
                changed = False
                if not tx.kind:
                    tx.kind = infer_kind(tx)
                    kinds_filled += 1
                    changed = True
                if tx.category_locked:
                    skipped_locked += 1
                elif self.categorizer.apply_to_transaction(session, tx):
                    updated += 1
                    changed = True
                if changed:
                    session.add(tx)
        return {
            "updated": updated,
            "skipped_locked": skipped_locked,
            "kinds_filled": kinds_filled,
        }

    @staticmethod
    def _apply_filters(
        stmt,
        *,
        uncategorized: bool = False,
        unassigned: bool = False,
        account_id: int | None = None,
        kind: str | None = None,
        search: str | None = None,
        tag: str | None = None,
        reimbursable: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ):
        if uncategorized:
            stmt = stmt.where(col(Transaction.category_id).is_(None))
        if unassigned:
            stmt = stmt.where(col(Transaction.account_id).is_(None))
        if account_id is not None:
            stmt = stmt.where(Transaction.account_id == account_id)
        if kind:
            stmt = stmt.where(Transaction.kind == kind)
        if reimbursable is True:
            stmt = stmt.where(col(Transaction.reimbursable) == True)  # noqa: E712
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                col(Transaction.description).ilike(like)
                | col(Transaction.merchant).ilike(like)
                | col(Transaction.notes).ilike(like)
            )
        if tag:
            stmt = stmt.where(col(Transaction.tags).ilike(f"%{tag}%"))
        if date_from is not None:
            stmt = stmt.where(col(Transaction.date) >= date_from)
        if date_to is not None:
            stmt = stmt.where(col(Transaction.date) <= date_to)
        return stmt

    @staticmethod
    def _join_stmt():
        return (
            select(Transaction, Bank, Category, Subcategory, Account)
            .join(Bank, col(Bank.id) == col(Transaction.bank_id))
            .outerjoin(Category, col(Category.id) == col(Transaction.category_id))
            .outerjoin(Subcategory, col(Subcategory.id) == col(Transaction.subcategory_id))
            .outerjoin(Account, col(Account.id) == col(Transaction.account_id))
        )

    @staticmethod
    def _map_transaction(
        tx: Transaction,
        bank: Bank,
        category: Category | None = None,
        subcategory: Subcategory | None = None,
        account: Account | None = None,
    ) -> Dict[str, Any]:
        """Map Transaction and related rows to a serializable dictionary."""
        return {
            "transaction_id": tx.transaction_id,
            "email_id": tx.email_id,
            "date": tx.date,
            "amount": tx.amount,
            "description": tx.description,
            "type": tx.type,
            "kind": tx.kind,
            "bank_id": tx.bank_id,
            "bank_name": bank.name,
            "account_id": tx.account_id,
            "account_name": account.name if account is not None else None,
            "category_id": tx.category_id,
            "subcategory_id": tx.subcategory_id,
            "category_name": category.name if category is not None else None,
            "subcategory_name": subcategory.name if subcategory is not None else None,
            "category_color": category.color if category is not None else None,
            "category_source": tx.category_source,
            "category_locked": bool(tx.category_locked),
            "merchant": tx.merchant,
            "reference": tx.reference,
            "notes": tx.notes,
            "tags": _parse_tags(tx.tags),
            "source": tx.source,
            "balance_applied": bool(tx.balance_applied),
            "excluded_from_budget": bool(tx.excluded_from_budget),
            "reimbursable": bool(tx.reimbursable),
            "currency": (tx.currency or "MXN").upper(),
            "amount_mxn": tx.amount_mxn,
        }


def _parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return [part.strip() for part in raw.split(",") if part.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _clean_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    seen: set[str] = set()
    cleaned: list[str] = []
    for tag in tags:
        name = tag.strip().lstrip("#")
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(name)
    return cleaned[:20]
