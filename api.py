"""FastAPI application for the Expense Tracker.

JSON endpoints are the contract for the web UI and a future mobile app.
Keep business logic here (via services), not in the frontend.
"""

from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.services.account_service import AccountService
from core.services.budget_service import BudgetService
from core.services.category_service import CategoryService
from core.services.statement_service import StatementService
from core.services.transaction_service import TransactionService
from database.database import Database
from main import run_sync
from models.category import CategoryCreate, CategoryRead, SubcategoryCreate, SubcategoryRead
from models.budget import BudgetUpsert
from models.statement import StatementRead
from models.transaction import TransactionCreate, TransactionUpdate
from models.account import (
    AccountCreate,
    AccountDetail,
    AccountRead,
    AccountTypeRead,
    AccountUpdate,
    BalanceUpdate,
    BankOption,
    DashboardRead,
)
from models.payment_coverage import PaymentCoverageUpsert


class PaginatedTransactions(BaseModel):
    """Paginated response containing transactions and total count."""

    total: int
    transactions: List[Dict[str, Any]]


app = FastAPI(title="Expense Tracker API", version="1.0.0")

# CORS configuration for frontend development. A native mobile app talks to
# this API directly and does not need CORS; keep origins explicit for browsers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5183"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    """Yield a Database and dispose it after the request."""
    db = Database()
    try:
        yield db
    finally:
        db.close()


def get_transaction_service(db: Database = Depends(get_db)):
    """Dependency that provides a TransactionService with a managed DB lifecycle."""
    return TransactionService(db)


def get_account_service(db: Database = Depends(get_db)):
    """Dependency that provides an AccountService with a managed DB lifecycle."""
    return AccountService(db)


def get_category_service(db: Database = Depends(get_db)):
    """Dependency that provides a CategoryService with a managed DB lifecycle."""
    return CategoryService(db)


def get_statement_service(db: Database = Depends(get_db)):
    return StatementService(db)


def get_budget_service(db: Database = Depends(get_db)):
    return BudgetService(db)


def _map_account_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail="Account not found")
    message = str(exc)
    status = 409 if "existe" in message.lower() else 400
    return HTTPException(status_code=status, detail=message)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/sync")
def sync_emails():
    """Trigger the Gmail sync process."""
    run_sync()
    return {"status": "ok"}


@app.get("/transactions", response_model=PaginatedTransactions)
def list_transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uncategorized: bool = Query(False),
    unassigned: bool = Query(False),
    account_id: Optional[int] = Query(None),
    kind: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    reimbursable: Optional[bool] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    service: TransactionService = Depends(get_transaction_service),
):
    """List transactions with pagination metadata."""
    filters = dict(
        uncategorized=uncategorized,
        unassigned=unassigned,
        account_id=account_id,
        kind=kind,
        search=search,
        tag=tag,
        reimbursable=reimbursable,
        date_from=datetime.combine(date_from, time.min) if date_from else None,
        date_to=datetime.combine(date_to, time.max) if date_to else None,
    )
    total = service.count_transactions(**filters)
    transactions = service.list_transactions(limit=limit, offset=offset, **filters)
    return PaginatedTransactions(total=total, transactions=transactions)


@app.post("/transactions", status_code=201)
def create_transaction(
    payload: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
):
    """Create a manual transaction."""
    payload.source = "manual"
    if not payload.email_id:
        payload.email_id = ""
    tx_id = service.save_transaction(payload)
    if tx_id is None:
        raise HTTPException(status_code=400, detail="No se pudo guardar la transacción")
    tx = service.get_transaction(tx_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@app.delete("/transactions/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
):
    try:
        service.delete_transaction(transaction_id)
    except LookupError as extra:
        raise HTTPException(status_code=404, detail=str(extra)) from extra
    return None


@app.post("/transactions/recategorize")
def recategorize_transactions(
    service: TransactionService = Depends(get_transaction_service),
):
    """Apply category rules to unlocked transactions."""
    return service.recategorize()


@app.get("/transactions/{transaction_id}")
def get_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service),
):
    """Get a single transaction by id."""
    tx = service.get_transaction(transaction_id)
    if tx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@app.patch("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    service: TransactionService = Depends(get_transaction_service),
):
    """Update notes, tags, kind, account, and/or category."""
    try:
        return service.update_transaction(transaction_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as extra:
        raise HTTPException(status_code=400, detail=str(extra)) from extra


@app.get("/account-types", response_model=List[AccountTypeRead])
def list_account_types(service: AccountService = Depends(get_account_service)):
    """Account types for create/edit forms."""
    return service.list_account_types()


@app.get("/banks", response_model=List[BankOption])
def list_banks(service: AccountService = Depends(get_account_service)):
    """Known banks plus any extra banks already stored."""
    return service.list_bank_options()


@app.get("/dashboard", response_model=DashboardRead)
def get_dashboard(service: AccountService = Depends(get_account_service)):
    """Home screen payload: assets, debts, and upcoming payments."""
    return service.get_dashboard()


@app.get("/accounts", response_model=List[AccountRead])
def list_accounts(
    active_only: bool = Query(False),
    service: AccountService = Depends(get_account_service),
):
    """List all accounts."""
    return service.list_accounts(active_only=active_only)


@app.post("/accounts", response_model=AccountDetail, status_code=201)
def create_account(
    payload: AccountCreate,
    service: AccountService = Depends(get_account_service),
):
    """Create an account and an opening balance snapshot."""
    try:
        return service.create_account(payload)
    except (ValueError, LookupError) as exc:
        raise _map_account_error(exc) from exc


@app.get("/accounts/{account_id}", response_model=AccountDetail)
def get_account(
    account_id: int,
    service: AccountService = Depends(get_account_service),
):
    """Get one account plus recent snapshots."""
    account = service.get_account(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@app.patch("/accounts/{account_id}", response_model=AccountDetail)
def update_account(
    account_id: int,
    payload: AccountUpdate,
    service: AccountService = Depends(get_account_service),
):
    """Update account metadata. Balance changes use POST /accounts/{id}/balance."""
    try:
        return service.update_account(account_id, payload)
    except (ValueError, LookupError) as extra:
        raise _map_account_error(extra) from extra


@app.get("/categories", response_model=List[CategoryRead])
def list_categories(service: CategoryService = Depends(get_category_service)):
    """Category tree for pickers and filters."""
    return service.list_tree()


@app.post("/categories", response_model=CategoryRead, status_code=201)
def create_category(
    payload: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
):
    try:
        return service.create_category(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/categories/{category_id}/subcategories", response_model=SubcategoryRead, status_code=201)
def create_subcategory(
    category_id: int,
    payload: SubcategoryCreate,
    service: CategoryService = Depends(get_category_service),
):
    try:
        return service.create_subcategory(category_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Category not found") from exc
    except ValueError as extra:
        raise HTTPException(status_code=409, detail=str(extra)) from extra


@app.get("/statements", response_model=List[StatementRead])
def list_statements(
    account_id: Optional[int] = Query(None),
    service: StatementService = Depends(get_statement_service),
):
    return service.list_statements(account_id=account_id)


@app.post("/statements", response_model=StatementRead)
async def upload_statement(
    account_id: int = Form(...),
    password: Optional[str] = Form(None),
    file: UploadFile = File(...),
    service: StatementService = Depends(get_statement_service),
):
    data = await file.read()
    try:
        return service.upload(account_id, file.filename or "statement.pdf", data, password)
    except LookupError as extra:
        raise HTTPException(status_code=404, detail=str(extra)) from extra
    except ValueError as extra:
        raise HTTPException(status_code=400, detail=str(extra)) from extra


@app.get("/statements/{statement_id}/reconcile")
def reconcile_statement_preview(
    statement_id: int,
    service: StatementService = Depends(get_statement_service),
):
    try:
        return service.reconcile_report(statement_id)
    except LookupError as extra:
        raise HTTPException(status_code=404, detail=str(extra)) from extra


@app.post("/statements/{statement_id}/reconcile")
def reconcile_statement_apply(
    statement_id: int,
    service: StatementService = Depends(get_statement_service),
):
    try:
        return service.apply_reconcile(statement_id)
    except LookupError as extra:
        raise HTTPException(status_code=404, detail=str(extra)) from extra


@app.post("/statements/{statement_id}/parse", response_model=StatementRead)
def parse_statement(
    statement_id: int,
    password: Optional[str] = Form(None),
    service: StatementService = Depends(get_statement_service),
):
    try:
        return service.parse(statement_id, password)
    except LookupError as extra:
        raise HTTPException(status_code=404, detail=str(extra)) from extra
    except ValueError as extra:
        raise HTTPException(status_code=400, detail=str(extra)) from extra


@app.put("/budgets")
def upsert_budget(
    payload: BudgetUpsert,
    service: BudgetService = Depends(get_budget_service),
):
    try:
        return service.upsert(payload)
    except LookupError as extra:
        raise HTTPException(status_code=404, detail=str(extra)) from extra


@app.get("/budgets")
def budget_report(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    service: BudgetService = Depends(get_budget_service),
):
    return service.month_report(year, month)


@app.get("/stats/by-category")
def spending_by_category(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    tx_type: str = Query("expense"),
    service: CategoryService = Depends(get_category_service),
):
    """Spending totals grouped by category for charts."""
    start = datetime.combine(date_from, time.min) if date_from else None
    end = datetime.combine(date_to, time.max) if date_to else None
    return service.spending_by_category(date_from=start, date_to=end, tx_type=tx_type)


@app.post("/accounts/{account_id}/payment-coverage", response_model=AccountDetail)
def set_payment_coverage(
    account_id: int,
    payload: PaymentCoverageUpsert,
    service: AccountService = Depends(get_account_service),
):
    try:
        return service.set_payment_coverage(account_id, payload)
    except LookupError as extra:
        raise HTTPException(status_code=404, detail=str(extra)) from extra
    except ValueError as extra:
        raise HTTPException(status_code=400, detail=str(extra)) from extra


@app.post("/accounts/{account_id}/balance", response_model=AccountDetail)
def set_account_balance(
    account_id: int,
    payload: BalanceUpdate,
    service: AccountService = Depends(get_account_service),
):
    """Set the current balance and record a manual snapshot."""
    try:
        return service.set_balance(account_id, payload)
    except (ValueError, LookupError) as extra:
        raise _map_account_error(extra) from extra
