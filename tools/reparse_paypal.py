"""Re-parse existing PayPal transactions using the updated parser."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure project root is importable when run as a script (python tools/reparse_paypal.py)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# pylint: disable=wrong-import-position
from sqlmodel import col, select

from core.parsers.paypal import PayPalParser
from database.database import Database
from models.transaction import Transaction

logger = logging.getLogger("expense_tracker")

DATA_DIR = _ROOT / "data"


def reparse():
    """Re-parse all PayPal transactions with NULL dates."""
    db = Database()
    parser = PayPalParser()
    updated = 0
    skipped = 0

    with db.session() as session:
        txs = session.exec(
            select(Transaction).where(
                Transaction.bank_id == 6,  # PayPal bank_id
                col(Transaction.date).is_(None),
            )
        ).all()

        print(f"Found {len(txs)} PayPal transactions with NULL dates")

        for tx in txs:
            # Find saved email file
            filepath = None
            for ext in (".html", ".txt"):
                candidate = DATA_DIR / f"{tx.email_id}{ext}"
                if candidate.exists():
                    filepath = candidate
                    break

            if not filepath:
                skipped += 1
                continue

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                body = f.read()

            email_message = {
                "subject": tx.description or "",
                "body_html": body,
                "body_plain": "",
            }

            result = parser.parse(email_message, tx.email_id)
            if result is None:
                skipped += 1
                continue

            # Update the transaction
            tx.date = result.date
            tx.amount = result.amount
            tx.description = result.description
            tx.merchant = result.merchant
            tx.reference = result.reference
            tx.type = result.type

            session.add(tx)
            updated += 1

        if updated > 0:
            session.commit()

    db.close()
    print(f"Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    reparse()
