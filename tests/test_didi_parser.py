"""Tests for the DiDi Préstamos email parser."""

from core.parsers.didi import DidiParser
from core.parsers.parser_helper import ParserHelper


PAYMENT_BODY = (
    "Hola, Francisco Javier Ramirez Rochin: Gracias por usar DiDi Préstamos. "
    "Recibimos tu pago de MXN$1,780.54. El plazo de tu siguiente pago vence el "
    "2026-08-28. Atentamente, DiDi Préstamos"
)

DEPOSIT_BODY = (
    "¡Gracias por elegir DiDi Préstamos! El préstamo que solicitaste se depositó "
    "correctamente en tu cuenta. El primer pago de MXN$250.00 vence el 13/01/2026, "
    "y el segundo pago de MXN$250.00 vence el 28/01/2026."
)

DATE_HEADER = "Thu, 13 Aug 2026 15:55:27 +0000"


def test_parser_helper_routes_didi_sender():
    parser = ParserHelper.get_parser_for_email(
        "=?UTF-8?b?RGlEaSBQcsOpc3RhbW9z?= <noreply@didiglobal.com>"
    )
    assert parser is not None
    assert parser.bank_name == "didi"


def test_parser_helper_routes_didi_card_sender():
    parser = ParserHelper.get_parser_for_email("DiDi Card <DiDi@mx.didiglobal.com>")
    assert parser is not None
    assert parser.bank_name == "didi"


def test_parse_payment_extracts_amount_date_and_next_due():
    parser = DidiParser()
    tx = parser.parse(
        {
            "subject": "Pago recibido",
            "body_plain": PAYMENT_BODY,
            "date": DATE_HEADER,
        },
        "msg-pago-1",
    )
    assert tx is not None
    assert tx.amount == 1780.54
    assert tx.type == "expense"
    assert tx.merchant == "DiDi Préstamos"
    assert tx.reference == "2026-08-28"
    assert tx.date is not None
    assert tx.date.year == 2026
    assert tx.date.month == 8
    assert tx.date.day == 13
    assert "Pago DiDi Préstamos" in tx.description


def test_parse_deposit_without_principal_is_skipped():
    parser = DidiParser()
    tx = parser.parse(
        {
            "subject": "Se depositó el préstamo en tu cuenta",
            "body_plain": DEPOSIT_BODY,
            "date": DATE_HEADER,
        },
        "msg-dep-1",
    )
    assert tx is None


def test_parse_deposit_with_explicit_principal():
    parser = DidiParser()
    tx = parser.parse(
        {
            "subject": "Se depositó el préstamo en tu cuenta",
            "body_plain": "El monto del préstamo MXN$5,000.00 se depositó en tu cuenta.",
            "date": DATE_HEADER,
        },
        "msg-dep-2",
    )
    assert tx is not None
    assert tx.type == "income"
    assert tx.amount == 5000.0


def test_skip_reminders_and_marketing():
    parser = DidiParser()
    for subject in (
        "Recuerda realizar tu pago",
        "Tu pago se encuentra vencido",
        "Tu último estado de cuenta está disponible",
        "Difiere con 30% de descuento",
        "Invitación Reembolso",
    ):
        tx = parser.parse(
            {"subject": subject, "body_plain": PAYMENT_BODY, "date": DATE_HEADER},
            "skip",
        )
        assert tx is None, subject


def test_slash_next_due_normalized():
    parser = DidiParser()
    tx = parser.parse(
        {
            "subject": "Pago recibido",
            "body_plain": "Recibimos tu pago de MXN$250.00. El plazo de tu siguiente pago vence el 13/01/2026.",
            "date": DATE_HEADER,
        },
        "msg-slash",
    )
    assert tx is not None
    assert tx.reference == "2026-01-13"
