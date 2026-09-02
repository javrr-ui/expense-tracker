"""Upload and parse bank statement PDFs."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, time
from pathlib import Path

from sqlmodel import col, select

from constants.account_types import AccountTypeName
from constants.banks import SupportedBanks
from core.parsers.statements.base import StatementPasswordError, extract_pdf_text, save_pdf
from core.parsers.statements.nubank import parse_nu_statement_text
from core.services.reconcile import ledger_window, match_score, pair_matches, should_enrich_description
from core.services.transaction_kind import infer_kind
from database.database import Database
from models.account import Account
from models.account_type import AccountType
from models.balance_snapshot import BalanceSnapshot
from models.bank import Bank
from models.statement import Statement, StatementRead
from models.transaction import Transaction

logger = logging.getLogger("expense_tracker")
STATEMENTS_DIR = Path("data/statements")


class StatementService:
    def __init__(self, db: Database):
        self.db = db

    def list_statements(self, account_id: int | None = None) -> list[StatementRead]:
        with self.db.session() as session:
            stmt = select(Statement).order_by(col(Statement.created_at).desc())
            if account_id is not None:
                stmt = stmt.where(Statement.account_id == account_id)
            rows = session.exec(stmt).all()
            return [self._to_read(row) for row in rows if row.id is not None]

    def upload(
        self,
        account_id: int,
        filename: str,
        data: bytes,
        password: str | None = None,
    ) -> StatementRead:
        with self.db.session() as session:
            account = session.get(Account, account_id)
            if account is None:
                raise LookupError("Account not found")
            stored = STATEMENTS_DIR / f"{uuid.uuid4().hex}_{filename}"
            save_pdf(data, stored)
            statement = Statement(
                account_id=account_id,
                source="upload",
                source_filename=filename,
                stored_path=str(stored),
                status="uploaded",
            )
            session.add(statement)
            session.flush()
            self._parse_row(session, statement, data, password or account.statement_password)
            session.add(statement)
            session.flush()
            return self._to_read(statement)

    def parse(self, statement_id: int, password: str | None = None) -> StatementRead:
        with self.db.session() as session:
            statement = session.get(Statement, statement_id)
            if statement is None:
                raise LookupError("Statement not found")
            account = session.get(Account, statement.account_id)
            path = Path(statement.stored_path or "")
            if not path.exists():
                raise ValueError("No se encontró el archivo del estado de cuenta")
            data = path.read_bytes()
            self._parse_row(
                session,
                statement,
                data,
                password or (account.statement_password if account else None),
            )
            if password and account is not None:
                account.statement_password = password
                session.add(account)
            session.add(statement)
            session.flush()
            return self._to_read(statement)

    def reconcile_report(self, statement_id: int) -> dict:
        with self.db.session() as session:
            statement, stmt_txs, ledger_txs = self._reconcile_sets(session, statement_id)
            pairs = pair_matches(stmt_txs, ledger_txs)
            matched_stmt = {id(stmt) for stmt, _led, _score in pairs}
            matched_led = {id(led) for _stmt, led, _score in pairs}
            items = []
            for stmt, led, score in pairs:
                items.append(
                    {
                        "status": "matched",
                        "score": score,
                        "statement_tx_id": stmt.transaction_id,
                        "ledger_tx_id": led.transaction_id,
                        "date": stmt.date.date().isoformat() if stmt.date else None,
                        "amount": stmt.amount,
                        "statement_description": stmt.description,
                        "ledger_description": led.description,
                        "ledger_source": led.source,
                    }
                )
            for stmt in stmt_txs:
                if id(stmt) in matched_stmt:
                    continue
                items.append(
                    {
                        "status": "only_statement",
                        "score": 0,
                        "statement_tx_id": stmt.transaction_id,
                        "ledger_tx_id": None,
                        "date": stmt.date.date().isoformat() if stmt.date else None,
                        "amount": stmt.amount,
                        "statement_description": stmt.description,
                        "ledger_description": None,
                        "ledger_source": None,
                    }
                )
            for led in ledger_txs:
                if id(led) in matched_led:
                    continue
                items.append(
                    {
                        "status": "only_ledger",
                        "score": 0,
                        "statement_tx_id": None,
                        "ledger_tx_id": led.transaction_id,
                        "date": led.date.date().isoformat() if led.date else None,
                        "amount": led.amount,
                        "statement_description": None,
                        "ledger_description": led.description,
                        "ledger_source": led.source,
                    }
                )
            return {
                "statement_id": statement.id,
                "account_id": statement.account_id,
                "matched": len(pairs),
                "only_statement": sum(1 for item in items if item["status"] == "only_statement"),
                "only_ledger": sum(1 for item in items if item["status"] == "only_ledger"),
                "items": items,
                "applied": False,
            }

    def apply_reconcile(self, statement_id: int) -> dict:
        with self.db.session() as session:
            statement, stmt_txs, ledger_txs = self._reconcile_sets(session, statement_id)
            pairs = pair_matches(stmt_txs, ledger_txs)
            merged = 0
            for stmt, led, _score in pairs:
                if led.account_id is None:
                    led.account_id = statement.account_id
                if should_enrich_description(led, stmt):
                    led.description = stmt.description
                if not led.kind and stmt.kind:
                    led.kind = stmt.kind
                if stmt.kind == "payment" and led.kind in {None, "purchase", "transfer"}:
                    led.kind = "payment"
                led.notes = (led.notes + " · " if led.notes else "") + f"conciliado estado #{statement.id}"
                stmt.balance_applied = False
                session.add(led)
                session.delete(stmt)
                merged += 1
            session.flush()
        report = self.reconcile_report(statement_id)
        report["applied"] = True
        report["merged"] = merged
        return report

    def _reconcile_sets(self, session, statement_id: int):
        statement = session.get(Statement, statement_id)
        if statement is None:
            raise LookupError("Statement not found")
        prefix = f"stmt:{statement.id}:"
        stmt_txs = session.exec(
            select(Transaction).where(col(Transaction.email_id).like(f"{prefix}%"))
        ).all()
        account = session.get(Account, statement.account_id)
        start, end = ledger_window(statement.period_start, statement.period_end)
        stmt = select(Transaction).where(
            Transaction.source != "statement",
        )
        if account is not None:
            stmt = stmt.where(
                (Transaction.bank_id == account.bank_id)
                & (
                    (col(Transaction.account_id).is_(None))
                    | (Transaction.account_id == account.id)
                )
            )
        if start is not None:
            stmt = stmt.where(col(Transaction.date) >= start)
        if end is not None:
            stmt = stmt.where(col(Transaction.date) <= end)
        ledger_txs = session.exec(stmt).all()
        return statement, list(stmt_txs), list(ledger_txs)

    def ingest_from_email(
        self,
        email_id: str,
        filename: str,
        data: bytes,
        bank_name: str,
        subject: str = "",
    ) -> StatementRead | None:
        """Store a Gmail PDF attachment as a statement when it looks like one."""
        if not data:
            return None
        blob = f"{subject} {filename}".lower()
        looks_like_statement = any(
            token in blob
            for token in ("estado de cuenta", "statement", "corte")
        )
        encrypted = _pdf_is_encrypted(data)
        if not looks_like_statement and not encrypted:
            return None

        with self.db.session() as session:
            existing = session.exec(select(Statement).where(Statement.email_id == email_id)).first()
            if existing is not None:
                return self._to_read(existing) if existing.id is not None else None
            account = _account_for_bank(session, bank_name)
            if account is None or account.id is None:
                logger.info("No unique account for statement email %s (%s)", email_id, bank_name)
                return None
            stored = STATEMENTS_DIR / f"{uuid.uuid4().hex}_{filename}"
            save_pdf(data, stored)
            statement = Statement(
                account_id=account.id,
                source="email",
                email_id=email_id,
                source_filename=filename,
                stored_path=str(stored),
                status="uploaded",
            )
            session.add(statement)
            session.flush()
            self._parse_row(session, statement, data, account.statement_password)
            session.add(statement)
            session.flush()
            logger.info(
                "Ingested statement email %s for account %s status=%s",
                email_id,
                account.id,
                statement.status,
            )
            return self._to_read(statement)

    def _parse_row(self, session, statement: Statement, data: bytes, password: str | None) -> None:
        try:
            text = extract_pdf_text(data, password)
        except StatementPasswordError as exc:
            statement.status = "needs_password"
            statement.error = str(exc)
            return
        except Exception as extra:
            statement.status = "failed"
            statement.error = str(extra)
            logger.error("Statement parse failed: %s", extra, exc_info=True)
            return

        account = session.get(Account, statement.account_id)
        bank = session.get(Bank, account.bank_id) if account is not None else None
        bank_name = bank.name if bank is not None else ""
        try:
            parsed = _parse_statement_text(bank_name, text)
        except ValueError as extra:
            statement.status = "unsupported"
            statement.error = str(extra)
            statement.raw_text = text[:50000]
            return

        statement.raw_text = parsed.raw_text[:50000] if parsed.raw_text else text[:50000]
        statement.period_start = parsed.period_start
        statement.period_end = parsed.period_end
        statement.previous_balance = parsed.previous_balance
        statement.closing_balance = parsed.closing_balance
        statement.minimum_payment = parsed.minimum_payment
        statement.due_date = parsed.due_date
        statement.parsed_at = datetime.now().replace(tzinfo=None)
        statement.error = None
        statement.status = "parsed"

        if account is not None:
            if parsed.minimum_payment is not None:
                account.minimum_payment = parsed.minimum_payment
            if parsed.due_date is not None:
                account.due_date_day = parsed.due_date.day
            if parsed.closing_balance is not None:
                account.current_balance = parsed.closing_balance
                period_end = parsed.period_end or parsed.due_date or datetime.now().date()
                account.last_snapshot_at = datetime.combine(period_end, time(23, 59, 59))
                session.add(
                    BalanceSnapshot(
                        account_id=account.id,  # type: ignore[arg-type]
                        amount=parsed.closing_balance,
                        as_of=account.last_snapshot_at,
                        source="statement",
                        note=f"Estado de cuenta {statement.source_filename or ''}".strip(),
                        statement_id=statement.id,
                    )
                )
            session.add(account)

        self._import_lines(session, statement, parsed.lines)

    def _import_lines(self, session, statement: Statement, lines) -> None:
        account = session.get(Account, statement.account_id)
        if account is None:
            return
        bank = session.get(Bank, account.bank_id)
        start, end = ledger_window(statement.period_start, statement.period_end)
        ledger_stmt = select(Transaction).where(Transaction.source != "statement")
        ledger_stmt = ledger_stmt.where(
            (Transaction.bank_id == account.bank_id)
            & (
                (col(Transaction.account_id).is_(None))
                | (Transaction.account_id == account.id)
            )
        )
        if start is not None:
            ledger_stmt = ledger_stmt.where(col(Transaction.date) >= start)
        if end is not None:
            ledger_stmt = ledger_stmt.where(col(Transaction.date) <= end)
        ledger = list(session.exec(ledger_stmt).all())
        used_ledger: set[int] = set()
        for index, line in enumerate(lines):
            external = f"stmt:{statement.id}:{index}"
            exists = session.exec(select(Transaction).where(Transaction.email_id == external)).first()
            if exists:
                continue
            candidate = Transaction(
                bank_id=account.bank_id,
                email_id=external,
                date=datetime.combine(line.date, datetime.min.time()) if line.date else None,
                amount=line.amount,
                description=line.description,
                type="income" if line.kind == "income" else "expense",
                kind=line.kind,
            )
            matched = None
            best = -1
            for led in ledger:
                if led.transaction_id in used_ledger:
                    continue
                score = match_score(candidate, led)
                if score > best:
                    best = score
                    matched = led
            if matched is not None and best >= 10:
                used_ledger.add(matched.transaction_id)
                if matched.account_id is None:
                    matched.account_id = statement.account_id
                if should_enrich_description(matched, candidate):
                    matched.description = line.description
                if line.kind == "payment":
                    matched.kind = "payment"
                session.add(matched)
                continue
            tx_type = "income" if line.kind == "income" else "expense"
            tx = Transaction(
                bank_id=bank.id if bank and bank.id else account.bank_id,
                email_id=external,
                date=datetime.combine(line.date, datetime.min.time()) if line.date else None,
                amount=line.amount,
                description=line.description,
                type=tx_type,
                kind=line.kind,
                account_id=statement.account_id,
                source="statement",
                balance_applied=True,
            )
            tx.kind = infer_kind(tx)
            session.add(tx)

    @staticmethod
    def _to_read(row: Statement) -> StatementRead:
        return StatementRead(
            id=row.id,  # type: ignore[arg-type]
            account_id=row.account_id,
            period_start=row.period_start,
            period_end=row.period_end,
            previous_balance=row.previous_balance,
            closing_balance=row.closing_balance,
            minimum_payment=row.minimum_payment,
            due_date=row.due_date,
            source=row.source,
            status=row.status,
            source_filename=row.source_filename,
            error=row.error,
            parsed_at=row.parsed_at,
        )


def _parse_statement_text(bank_name: str, text: str):
    if bank_name == SupportedBanks.NUBANK:
        return parse_nu_statement_text(text)
    raise ValueError(f"Aún no hay parser de estado de cuenta para {bank_name or 'este banco'}")


def _pdf_is_encrypted(data: bytes) -> bool:
    try:
        from pypdf import PdfReader
        from io import BytesIO

        reader = PdfReader(BytesIO(data))
        return bool(reader.is_encrypted)
    except Exception:
        return False


def _account_for_bank(session, bank_name: str) -> Account | None:
    bank = session.exec(select(Bank).where(Bank.name == bank_name)).first()
    if bank is None or bank.id is None:
        return None
    rows = session.exec(
        select(Account, AccountType)
        .join(AccountType, col(AccountType.id) == col(Account.account_type_id))
        .where(Account.bank_id == bank.id, col(Account.is_active) == True)  # noqa: E712
    ).all()
    if len(rows) == 1:
        return rows[0][0]
    cards = [account for account, account_type in rows if account_type.name == AccountTypeName.CREDIT_CARD]
    if len(cards) == 1:
        return cards[0]
    return None
