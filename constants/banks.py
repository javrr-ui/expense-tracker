"""Constants related to supported banks and their notification email addresses.

This module defines:
- SupportedBanks: An enum of all banks currently supported by the expense tracker.
- bank_emails: A mapping from each bank to the known email addresses used for transaction
  notifications.
"""

from enum import StrEnum


class SupportedBanks(StrEnum):
    """Supported bank identifiers used throughout the expense tracker.

    This enum defines string-based identifiers for each supported financial institution.
    Using StrEnum ensures type safety while allowing string comparisons and serialization.
    """

    HEY_BANCO = "hey_banco"
    NUBANK = "nubank"
    RAPPI = "rappi"
    PAYPAL = "paypal"
    BANORTE = "banorte"
    MERCADO_PAGO = "mercado_pago"
    AMEX = "amex"
    DIDI = "didi"
    BANAMEX = "banamex"


BANK_DISPLAY_NAMES = {
    SupportedBanks.HEY_BANCO: "Hey Banco",
    SupportedBanks.NUBANK: "Nu",
    SupportedBanks.RAPPI: "RappiCard",
    SupportedBanks.PAYPAL: "PayPal",
    SupportedBanks.BANORTE: "Banorte",
    SupportedBanks.MERCADO_PAGO: "Mercado Pago",
    SupportedBanks.AMEX: "American Express",
    SupportedBanks.DIDI: "DiDi",
    SupportedBanks.BANAMEX: "Banamex",
}


def bank_display_name(bank_name: str) -> str:
    """Human-readable bank name for API clients (web and future mobile)."""
    try:
        return BANK_DISPLAY_NAMES[SupportedBanks(bank_name)]
    except ValueError:
        return bank_name


bank_emails = {
    SupportedBanks.HEY_BANCO: [
        "noreply@hey.inc",
        "alertas@hey.inc",
        "noreply@heybanco.com",
        "alertas@heybanco.com",
    ],
    SupportedBanks.NUBANK: ["nu@nu.com.mx"],
    SupportedBanks.RAPPI: [
        "rappi.nreply@rappi.com",
        "no-reply@mailing.rappicard.com.mx",
    ],
    SupportedBanks.PAYPAL: [
        "service@paypal.com.mx",
        "service@paypal.com",
        "service@intl.paypal.com",
        "paypal@paypal.com",
        "paypal@paypal.com.mx",
        "member@paypal.com.mx",
        "member@paypal.com",
    ],
    SupportedBanks.BANORTE: ["notificaciones@banorte.com"],
    SupportedBanks.MERCADO_PAGO: ["info@mercadopago.com"],
    SupportedBanks.AMEX: ["AmericanExpress@welcome.americanexpress.com"],
    SupportedBanks.DIDI: [
        "noreply@didiglobal.com",
        "noreply@mx.didiglobal.com",
        "didi@mx.didiglobal.com",
        "didiglobal.com",
    ],
    SupportedBanks.BANAMEX: [
        "notificaciones@banamex.com",
        "notificaciones@citibanamex.com",
    ],
}
