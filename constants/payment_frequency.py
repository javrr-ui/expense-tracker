"""Payment recurrence frequencies for loans and other liabilities."""

from enum import StrEnum


class PaymentFrequency(StrEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


PAYMENT_FREQUENCY_LABELS = {
    PaymentFrequency.WEEKLY: "Cada semana",
    PaymentFrequency.BIWEEKLY: "Cada 2 semanas",
    PaymentFrequency.MONTHLY: "Cada mes",
}

VALID_FREQUENCIES = frozenset(PaymentFrequency)
