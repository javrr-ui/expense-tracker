"""Transaction service for managing transactions."""

from typing import Optional
import logging
from sqlmodel import select
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
        """Save a transaction to the database."""
        with self.db.session() as session:
            try:
                stmt = select(Bank).where(Bank.name == transaction.bank_name)
                bank = session.exec(stmt).first()

                if bank is None:
                    bank = Bank(name=transaction.bank_name)
                    session.add(bank)
                    session.commit()  # commit so we get the ID
                    session.refresh(bank)

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
                    tx.category_id,
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
