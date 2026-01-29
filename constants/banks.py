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
    SupportedBanks.PAYPAL: ["service@paypal.com.mx"],
    SupportedBanks.BANORTE: ["notificaciones@banorte.com"],
    SupportedBanks.MERCADO_PAGO: ["info@mercadopago.com"],
}
