from core.parsers.paypal import PayPalParser


def test_paypal_extracts_usd_and_mxn_equivalent():
    body = """
    <p>Ha pagado $6.00&nbsp;USD a Vultr</p>
    <span>$6.00&nbsp;USD</span>
    <span>$107.48&nbsp;MXN</span>
    <span>Tasa de conversión de PayPal: 1 MXN = 0.0558 USD</span>
    """
    amount, currency, amount_mxn = PayPalParser._extract_amount(body)
    assert amount == 6.0
    assert currency == "USD"
    assert amount_mxn == 107.48
