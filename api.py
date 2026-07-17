"""FastAPI application for the Expense Tracker."""

from typing import Any, Dict, List

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.services.transaction_service import TransactionService
from database.database import Database
from main import run_sync


class PaginatedTransactions(BaseModel):
    """Paginated response containing transactions and total count."""

    total: int
    transactions: List[Dict[str, Any]]


app = FastAPI(title="Expense Tracker API", version="1.0.0")

# CORS configuration for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5183"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_transaction_service():
    """Dependency that provides a TransactionService with a managed DB lifecycle."""
    db = Database()
    try:
        yield TransactionService(db)
    finally:
        db.close()


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
    service: TransactionService = Depends(get_transaction_service),
):
    """List transactions with pagination metadata."""
    total = service.count_transactions()
    transactions = service.list_transactions(limit=limit, offset=offset)
    return PaginatedTransactions(total=total, transactions=transactions)


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
