from typing import Literal
from enum import StrEnum

class SupportedBanks(StrEnum):
    HEY_BANCO = "hey_banco"
    NUBANK = "nubank"
    RAPPI = "rappi"
    PAYPAL = "paypal"
    BANORTE = "banorte"

bank_emails = {
    SupportedBanks.HEY_BANCO: ['noreply@hey.inc', 'alertas@hey.inc', 'noreply@heybanco.com', 'alertas@heybanco.com'],
    SupportedBanks.NUBANK: ['nu@nu.com.mx'],
    SupportedBanks.RAPPI: ['rappi.nreply@rappi.com', 'no-reply@mailing.rappicard.com.mx'],
    SupportedBanks.PAYPAL: ['service@paypal.com.mx'],
    SupportedBanks.BANORTE: ['notificaciones@banorte.com']
}