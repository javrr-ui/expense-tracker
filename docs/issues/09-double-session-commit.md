# Code Smell: Double Session Commit

**Labels:** `code-quality`, `performance`, `medium-priority`, `database`  
**Type:** Design Issue

## Description

The `save_transaction` method commits the database session twice: once for the bank entity (line 33) and once for the transaction (line 50). This is inefficient and breaks transaction atomicity.

## Location

- `core/services/transaction_service.py` (lines 33, 50)

## Current Code

```python
def save_transaction(self, transaction: TransactionCreate) -> Optional[int]:
    """Save a transaction to the database."""
    with self.db.session() as session:
        try:
            stmt = select(Bank).where(Bank.name == transaction.bank_name)
            bank = session.exec(stmt).first()

            if bank is None:
                bank = Bank(name=transaction.bank_name)
                session.add(bank)
                session.commit()  # ← First commit
                session.refresh(bank)

            tx = Transaction(
                bank_id=bank.id,
                # ... other fields
            )

            session.add(tx)
            session.commit()  # ← Second commit
            session.refresh(tx)
            # ...
```

## Impact

- **Performance:** Two database commits when one would suffice
- **Atomicity:** Bank and transaction aren't saved atomically
- **Failure Scenario:** If transaction save fails, bank is already committed
- **Database Load:** Extra roundtrips to database

## Proposed Solution

Use `session.flush()` to get the bank ID without committing:

```python
def save_transaction(self, transaction: TransactionCreate) -> Optional[int]:
    """Save a transaction to the database."""
    with self.db.session() as session:
        try:
            stmt = select(Bank).where(Bank.name == transaction.bank_name)
            bank = session.exec(stmt).first()

            if bank is None:
                bank = Bank(name=transaction.bank_name)
                session.add(bank)
                session.flush()  # ← Flush to get ID, don't commit yet
                # No need to refresh, flush makes ID available

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
            # Let the context manager handle commit
            # This commits both bank and transaction atomically
            
        except SQLAlchemyError as e:
            # Rollback will undo both bank and transaction
            session.rollback()
            logger.error("Database error during save: %s", e, exc_info=True)
            return None
```

## Better Alternative

The context manager in `database.py` already handles commits. We can simplify further:

```python
def save_transaction(self, transaction: TransactionCreate) -> Optional[int]:
    """Save a transaction to the database."""
    with self.db.session() as session:
        # Get or create bank
        stmt = select(Bank).where(Bank.name == transaction.bank_name)
        bank = session.exec(stmt).first()

        if bank is None:
            bank = Bank(name=transaction.bank_name)
            session.add(bank)
            session.flush()  # Get ID without committing

        # Create transaction
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
        session.flush()  # Get transaction ID
        
        logger.info(
            "Transaction added [ID: %s] | %s | %s | %s | Category: %s | Subcategory: %s",
            tx.transaction_id,
            tx.amount,
            tx.date,
            tx.description,
            tx.category_id,
            tx.subcategory_id,  # Fixed in #10
        )
        
        return tx.transaction_id
        # Context manager commits here (single commit for both)
```

## Acceptance Criteria

- [ ] Replace `session.commit()` calls with `session.flush()`
- [ ] Remove explicit commits; rely on context manager
- [ ] Verify both bank and transaction are still saved
- [ ] Test rollback behavior on error
- [ ] Confirm performance improvement (optional)
- [ ] Update any related documentation

## Benefits

- **Atomicity:** Bank and transaction saved in single transaction
- **Performance:** One commit instead of two
- **Consistency:** Better error handling and rollback behavior
- **Cleaner Code:** Removes manual commit management

## Related Issues

- #10 (Logging bug with category_id) - Same method
