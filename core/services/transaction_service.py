"""Transaction service for managing transactions."""

from typing import Optional, List, Dict, Any
import logging
from sqlmodel import col, desc, func, select
from sqlalchemy.exc import SQLAlchemyError

from database.database import Database
from models.transaction import TransactionCreate, Transaction
from models.bank import Bank


logger = logging.getLogger("expense_tracker")


class TransactionService:
    """Service for managing transactions in the database."""

    def __init__(self, db: Database):
        """Initialize with a Database instance."""
        self.db = db

    def save_transaction(self, transaction: TransactionCreate) -> Optional[int]:
        """Save a transaction to the database. Skips duplicates by email_id."""
        with self.db.session() as session:
            try:
                # Skip if this email was already processed
                existing = session.exec(
                    select(Transaction).where(Transaction.email_id == transaction.email_id)
                ).first()
                if existing:
                    logger.info("Duplicate email_id skipped: %s", transaction.email_id)
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
                    email_id=transaction.email_id,
                    date=transaction.date,
                    amount=transaction.amount,
                    category_id=None,
                    subcategory_id=None,
                    description=transaction.description,
                    type=transaction.type,
                    merchant=transaction.merchant,
                    reference=transaction.reference,
                )

                session.add(tx)
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

    def list_transactions(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List transactions with their bank name."""
        with self.db.session() as session:
            try:
                stmt = (
                    select(Transaction, Bank)
                    .join(Bank, col(Bank.id) == col(Transaction.bank_id))
                    .order_by(
                        desc(col(Transaction.date)),
                        desc(col(Transaction.transaction_id)),
                    )
                    .offset(offset)
                    .limit(limit)
                )
                results = session.exec(stmt).all()
                return [self._map_transaction(tx, bank) for tx, bank in results]
            except SQLAlchemyError as e:
                logger.error("SQLAlchemy database error during list: %s", e, exc_info=True)
                return []

    def count_transactions(self) -> int:
        """Return the total number of transactions."""
        with self.db.session() as session:
            try:
                stmt = select(func.count()).select_from(Transaction)  # pylint: disable=not-callable
                return session.exec(stmt).one()
            except SQLAlchemyError as e:
                logger.error("SQLAlchemy database error during count: %s", e, exc_info=True)
                return 0

    def get_transaction(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """Get a single transaction by id."""
        with self.db.session() as session:
            try:
                stmt = (
                    select(Transaction, Bank)
                    .join(Bank, col(Bank.id) == col(Transaction.bank_id))
                    .where(Transaction.transaction_id == transaction_id)
                )
                result = session.exec(stmt).first()
                if result is None:
                    return None
                tx, bank = result
                return self._map_transaction(tx, bank)
            except SQLAlchemyError as e:
                logger.error("SQLAlchemy database error during get: %s", e, exc_info=True)
                return None

    @staticmethod
    def _map_transaction(tx: Transaction, bank: Bank) -> Dict[str, Any]:
        """Map Transaction and Bank to a serializable dictionary."""
        return {
            "transaction_id": tx.transaction_id,
            "email_id": tx.email_id,
            "date": tx.date,
            "amount": tx.amount,
            "description": tx.description,
            "type": tx.type,
            "bank_id": tx.bank_id,
            "bank_name": bank.name,
            "category_id": tx.category_id,
            "subcategory_id": tx.subcategory_id,
            "merchant": tx.merchant,
            "reference": tx.reference,
        }
