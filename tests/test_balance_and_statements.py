"""Account balance deltas and Nu statement text parsing."""

from contextlib import contextmanager
from datetime import datetime, timedelta

from constants.account_types import AccountTypeName
from core.parsers.statements.nubank import parse_nu_statement_text
from core.services.account_service import AccountService
from core.services.transaction_service import TransactionService
from database.database import Database
from models.account import AccountCreate, BalanceUpdate
from models.transaction import TransactionCreate, TransactionUpdate


@contextmanager
def _db():
    db = Database("sqlite://")
    try:
        yield db
    finally:
        db.close()


def test_liability_purchase_and_payment_adjust_balance():
    with _db() as db:
        accounts = AccountService(db)
        txs = TransactionService(db)
        created = accounts.create_account(
            AccountCreate(
                name="Nu Crédito",
                bank_name="nubank",
                account_type=AccountTypeName.CREDIT_CARD,
                current_balance=1000,
            )
        )
        snapshot_time = datetime(2026, 8, 31, 12, 0, 0)
        accounts.set_balance(
            created.id,
            BalanceUpdate(amount=1000, as_of=snapshot_time),
        )
        purchase = txs.save_transaction(
            TransactionCreate(
                email_id="p1",
                bank_name="nubank",
                amount=100,
                description="OXXO",
                type="expense",
                kind="purchase",
                date=datetime(2026, 9, 1, 12, 0, 0),
            )
        )
        assert purchase is not None
        nu = accounts.get_account(created.id)
        assert nu is not None
        assert nu.current_balance == 1100

        pay = txs.save_transaction(
            TransactionCreate(
                email_id="pay1",
                bank_name="nubank",
                amount=200,
                description="Pago tarjeta de crédito Nu",
                type="expense",
                kind="payment",
                date=datetime(2026, 9, 1, 13, 0, 0),
            )
        )
        assert pay is not None
        nu = accounts.get_account(created.id)
        assert nu is not None
        assert nu.current_balance == 900


def test_historical_assign_does_not_move_balance():
    with _db() as db:
        accounts = AccountService(db)
        txs = TransactionService(db)
        created = accounts.create_account(
            AccountCreate(
                name="Nu 2",
                bank_name="nubank",
                account_type=AccountTypeName.CREDIT_CARD,
                current_balance=500,
            )
        )
        old = txs.save_transaction(
            TransactionCreate(
                email_id="old1",
                bank_name="hey_banco",
                amount=50,
                description="viejo",
                type="expense",
                date=datetime(2020, 1, 1),
            )
        )
        txs.update_transaction(old, TransactionUpdate(account_id=created.id))
        nu = accounts.get_account(created.id)
        assert nu is not None
        assert nu.current_balance == 500


def test_parse_nu_statement_text_extracts_totals_and_lines():
    sample = """
    Estado de cuenta
    Periodo del 01/08/2026 al 31/08/2026
    Saldo anterior: $1,000.00
    Saldo al corte: $1,250.50
    Pago mínimo: $200.00
    Fecha límite de pago: 15/09/2026
    05/08/2026 OXXO INSURGENTES $120.00
    10/08/2026 PAGO RECIBIDO $500.00
    """
    parsed = parse_nu_statement_text(sample)
    assert parsed.closing_balance == 1250.50
    assert parsed.previous_balance == 1000.00
    assert parsed.minimum_payment == 200.00
    assert parsed.due_date.isoformat() == "2026-09-15"
    assert parsed.period_start.isoformat() == "2026-08-01"
    assert len(parsed.lines) >= 2
    assert parsed.lines[1].kind == "payment"


def test_parse_nu_checking_statement_july_layout():
    sample = """
    Periodo: del 01 al 31 jul 2026
    Saldo inicial $7,032.82
    Saldo al generar este estado de cuenta $3,194.01
    Detalle de movimientos en tu cuenta
    31 JUL 2026 Macamen Transferencia -$315.00
    Transferencia SPEI, Hora: 14:21:56, Enviado a BANORTE.
    31 JUL 2026 TELNOR VENTA INT MU Compra -$778.00
    30 JUL 2026 JESUS ALFREDO NAVARRO LOPEZ MERCADO*PAGO +$52.20
    27 JUL 2026 Pago a tu tarjeta de crédito Nu -$120.00
    28 JUL 2026 Cajero BANCOMER S.A. Retiro de efectivo -$238.28
    Comisión BANCOMER S.A. $38.28
    FRANCISCO JAVIER RAMIREZ ROCHIN Transferencia de
    17 JUL 2026 +$200.00
    """
    parsed = parse_nu_statement_text(sample)
    assert parsed.period_start.isoformat() == "2026-07-01"
    assert parsed.period_end.isoformat() == "2026-07-31"
    assert parsed.previous_balance == 7032.82
    assert parsed.closing_balance == 3194.01
    kinds = {item.description: item.kind for item in parsed.lines}
    assert kinds["Macamen Transferencia"] == "transfer"
    assert kinds["TELNOR VENTA INT MU Compra"] == "purchase"
    assert kinds["JESUS ALFREDO NAVARRO LOPEZ MERCADO*PAGO"] == "income"
    assert kinds["Pago a tu tarjeta de crédito Nu"] == "payment"
    incoming = next(item for item in parsed.lines if item.amount == 200)
    assert incoming.kind == "income"
    assert "FRANCISCO" in incoming.description
    assert all("Comisión BANCOMER" not in item.description for item in parsed.lines)


def test_parse_nu_credit_card_statement_layout():
    sample = """
    Producto: Tarjeta de Crédito Nu, Oro
    Periodo: 14 JUL 2026 al 13 AGO 2026
    Fecha de corte: 13 AGO 2026
    Fecha límite de pago1: Lunes, 24 AGO 2026
    Pago para no generar intereses2:
    $22,964.77
    Pago mínimo4: $2,465.47
    Adeudo del periodo anterior = $22,982.66
    CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)
    24 JUL 2026 24 JUL 2026 Crédito de saldo revolvente | RFC: S.I. -$19,660.04
    24 JUL 2026 24 JUL 2026 Saldo revolvente | RFC: S.I. +$19,660.04
    13 JUL 2026 14 JUL 2026 Tacos El Panzon Rest | RFC: S.I. +$120.00
    14 JUL 2026 14 JUL 2026 ¡Grácias por tu pago! | RFC: S.I. -$300.00
    14 AGO 2026 14 AGO 2026 Intereses ordinarios | RFC: S.I. +$1,853.15
    """
    parsed = parse_nu_statement_text(sample)
    assert parsed.period_start.isoformat() == "2026-07-14"
    assert parsed.period_end.isoformat() == "2026-08-13"
    assert parsed.due_date.isoformat() == "2026-08-24"
    assert parsed.closing_balance == 22964.77
    assert parsed.minimum_payment == 2465.47
    assert parsed.previous_balance == 22982.66
    assert [item.description for item in parsed.lines] == [
        "Tacos El Panzon Rest",
        "¡Grácias por tu pago!",
        "Intereses ordinarios",
    ]
    assert parsed.lines[0].kind == "purchase"
    assert parsed.lines[1].kind == "payment"
    assert parsed.lines[2].kind == "fee"


def test_reconcile_pairs_email_payment_with_statement_line():
    from core.services.reconcile import pair_matches
    from models.transaction import Transaction

    statement_tx = Transaction(
        bank_id=1,
        email_id="stmt:1:0",
        date=datetime(2026, 7, 15),
        amount=200,
        description="Pago a tu tarjeta de crédito Nu",
        type="expense",
        kind="payment",
        source="statement",
    )
    email_tx = Transaction(
        bank_id=1,
        email_id="gmail-abc",
        date=datetime(2026, 7, 15, 10, 3),
        amount=200,
        description="Pago tarjeta de crédito Nu",
        type="expense",
        source="email",
    )
    other = Transaction(
        bank_id=1,
        email_id="gmail-other",
        date=datetime(2026, 7, 15, 12, 0),
        amount=50,
        description="Pago tarjeta de crédito Nu",
        type="expense",
        source="email",
    )
    pairs = pair_matches([statement_tx], [email_tx, other])
    assert len(pairs) == 1
    assert pairs[0][1].email_id == "gmail-abc"


def test_reconcile_does_not_pair_purchase_with_card_payment():
    from core.services.reconcile import pair_matches
    from models.transaction import Transaction

    tacos = Transaction(
        bank_id=1,
        email_id="stmt:2:1",
        date=datetime(2026, 8, 12),
        amount=120,
        description="Tacos El Panzon Rest",
        type="expense",
        kind="purchase",
        source="statement",
    )
    payment = Transaction(
        bank_id=1,
        email_id="gmail-pay",
        date=datetime(2026, 8, 13, 9, 0),
        amount=120,
        description="Pago tarjeta de crédito Nu",
        type="expense",
        kind="payment",
        source="email",
    )
    assert pair_matches([tacos], [payment]) == []


def test_delete_reverses_applied_balance():
    with _db() as db:
        accounts = AccountService(db)
        txs = TransactionService(db)
        created = accounts.create_account(
            AccountCreate(
                name="Nu 3",
                bank_name="nubank",
                account_type=AccountTypeName.CREDIT_CARD,
                current_balance=1000,
            )
        )
        accounts.set_balance(
            created.id,
            BalanceUpdate(amount=1000, as_of=datetime(2026, 8, 31, 12, 0, 0)),
        )
        tx_id = txs.save_transaction(
            TransactionCreate(
                email_id="del1",
                bank_name="nubank",
                amount=80,
                description="OXXO",
                type="expense",
                kind="purchase",
                date=datetime(2026, 9, 1, 12, 0, 0),
            )
        )
        assert tx_id is not None
        nu = accounts.get_account(created.id)
        assert nu is not None
        assert nu.current_balance == 1080
        txs.delete_transaction(tx_id)
        nu = accounts.get_account(created.id)
        assert nu is not None
        assert nu.current_balance == 1000


def test_manual_empty_email_id_saves_twice():
    with _db() as db:
        txs = TransactionService(db)
        first = txs.save_transaction(
            TransactionCreate(
                email_id="",
                bank_name="nubank",
                amount=20,
                description="kermes",
                type="expense",
                source="manual",
            )
        )
        second = txs.save_transaction(
            TransactionCreate(
                email_id="",
                bank_name="nubank",
                amount=30,
                description="kermes 2",
                type="expense",
                source="manual",
            )
        )
        assert first is not None
        assert second is not None
        assert first != second


def test_budget_vs_actual_for_month():
    from core.services.budget_service import BudgetService
    from core.services.category_service import CategoryService
    from models.budget import BudgetUpsert

    with _db() as db:
        txs = TransactionService(db)
        categories = CategoryService(db).list_tree()
        comida = next(item for item in categories if item.name == "Comida")
        BudgetService(db).upsert(
            BudgetUpsert(category_id=comida.id, year=2026, month=9, amount=1000)
        )
        tx_id = txs.save_transaction(
            TransactionCreate(
                email_id="b1",
                bank_name="nubank",
                amount=250,
                description="super",
                type="expense",
                kind="purchase",
                date=datetime(2026, 9, 2, 12, 0, 0),
            )
        )
        assert tx_id is not None
        txs.update_transaction(
            tx_id,
            TransactionUpdate(category_id=comida.id, subcategory_id=None),
        )
        report = BudgetService(db).month_report(2026, 9)
        row = next(item for item in report["items"] if item["category_id"] == comida.id)
        assert row["budget"] == 1000
        assert row["spent"] == 250
        assert row["remaining"] == 750


def test_extract_pdf_attachments_from_multipart_email():
    from email.message import EmailMessage

    from core.fetch_emails import extract_pdf_attachments

    message = EmailMessage()
    message["Subject"] = "Tu estado de cuenta"
    message["From"] = "nu@nu.com.mx"
    message.set_content("adjunto")
    message.add_attachment(b"%PDF-1.4 fake", maintype="application", subtype="pdf", filename="corte.pdf")
    attachments = extract_pdf_attachments(message)
    assert len(attachments) == 1
    assert attachments[0][0] == "corte.pdf"
    assert attachments[0][1].startswith(b"%PDF")
