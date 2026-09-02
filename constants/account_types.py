"""Account type identifiers used for liabilities vs assets."""

from enum import StrEnum


class AccountTypeName(StrEnum):
    """Canonical account type names stored in `account_type.name`."""

    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    CHECKING = "checking"
    WALLET = "wallet"


LIABILITY_ACCOUNT_TYPES = frozenset(
    {
        AccountTypeName.CREDIT_CARD,
        AccountTypeName.LOAN,
    }
)

ASSET_ACCOUNT_TYPES = frozenset(
    {
        AccountTypeName.CHECKING,
        AccountTypeName.WALLET,
    }
)

ACCOUNT_TYPE_SEED: list[tuple[str, str]] = [
    (AccountTypeName.CREDIT_CARD, "Tarjeta de crédito"),
    (AccountTypeName.LOAN, "Préstamo"),
    (AccountTypeName.CHECKING, "Cuenta de cheques / débito"),
    (AccountTypeName.WALLET, "Monedero (PayPal, Mercado Pago, etc.)"),
]


def is_liability_type(account_type: str) -> bool:
    """Return True when the account type represents money owed."""
    return account_type in LIABILITY_ACCOUNT_TYPES
