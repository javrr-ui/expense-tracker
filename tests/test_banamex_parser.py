from core.parsers.banamex import BanamexParser
from core.parsers.parser_helper import ParserHelper

PURCHASE_HTML = """
<html><body>
<p><b>Se realiz&oacute; la siguiente operaci&oacute;n: Retiro / Compra</b></p>
<p>Monto</p><p><b>$1,200.00</b></p>
<p>Establecimiento</p><p><b>RENOV MEMB COSTCO CR  HUI</b></p>
<p>Fecha y hora</p><p><b>2026/06/12 06:47:04 AM</b></p>
<p>No. Autorizaci&oacute;n</p><p><b>472023</b></p>
<p>M&iacute;nimo a pagar*</p><p><b>$1,330.00</b></p>
</body></html>
"""

DEPOSIT_HTML = """
<html><body>
<p><b>Se realiz&oacute; la siguiente operaci&oacute;n: Dep&oacute;sito a cuenta o tarjeta</b></p>
<p>Monto</p><p><b>$ 1,600.00</b></p>
<p>Medio</p><p><b>SPEI 008956</b></p>
<p>Fecha y hora</p><p><b>11 Agosto 2026 / 00:35:22</b></p>
<p>No. Autorizaci&oacute;n</p><p><b>703317</b></p>
<p>M&iacute;nimo a pagar*</p><p><b>$ 1,570.00</b></p>
</body></html>
"""


def test_routes_banamex_sender():
    parser = ParserHelper.get_parser_for_email("Notificaciones <notificaciones@banamex.com>")
    assert parser is not None
    assert parser.bank_name == "banamex"


def test_parse_purchase():
    tx = BanamexParser().parse(
        {"subject": "Retiro/Compra con tarjeta Banamex", "body_html": PURCHASE_HTML},
        "banamex-buy-1",
    )
    assert tx is not None
    assert tx.type == "expense"
    assert tx.kind == "purchase"
    assert tx.amount == 1200.00
    assert tx.merchant == "RENOV MEMB COSTCO CR HUI"
    assert tx.reference == "472023"
    assert tx.date.year == 2026
    assert tx.date.month == 6
    assert tx.date.day == 12
    assert tx.date.hour == 6


def test_parse_deposit_uses_operation_amount_not_minimum():
    tx = BanamexParser().parse(
        {"subject": "Depósito a Cuenta o Tarjeta Banamex", "body_html": DEPOSIT_HTML},
        "banamex-dep-1",
    )
    assert tx is not None
    assert tx.type == "income"
    assert tx.amount == 1600.00
    assert tx.description == "SPEI 008956"
    assert tx.reference == "703317"
    assert tx.date.month == 8
    assert tx.date.day == 11
    assert tx.date.hour == 0


def test_skips_preferences_email():
    tx = BanamexParser().parse(
        {
            "subject": "Cambio de Preferencias de Notificaciones",
            "body_html": "<p>Se han modificado tus datos de contacto</p>",
        },
        "banamex-pref",
    )
    assert tx is None
