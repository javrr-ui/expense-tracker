"""Abstract base class for parsing bank transaction emails.

This module provides the BaseBankParser class, which serves as a foundation
for creating bank-specific parsers. It includes an abstract method for parsing
emails and a helper method for decoding email subjects.
"""

from abc import ABC, abstractmethod
from email.header import decode_header

from models.transaction import TransactionCreate


class BaseBankParser(ABC):
    """Abstract base class for bank-specific email parsers.

    This class defines the interface for parsing bank emails to extract
    transaction data. Subclasses must implement the parse method and
    can utilize the _decode_subject helper for handling encoded subjects.

    Attributes:
        bank_name (str): The name of the bank (default: "generic").
    """

    bank_name = "generic"

    @abstractmethod
    def parse(self, email_message, email_id: str) -> TransactionCreate | None:
        """Parse an email message to extract a transaction.

        This method must be implemented by subclasses to handle bank-specific
        email formats and extract relevant transaction details.

        Args:
            email_message (dict): The parsed email message containing keys like
                'subject', 'body_plain', 'body_html', 'date', etc.
            email_id (str): The unique identifier of the email.

        Returns:
            Transaction | None: A Transaction object if a valid transaction
            is found in the email, otherwise None.
        """

    def _decode_subject(self, subject: str) -> str:
        """Decode an email subject header, handling multiple encodings.

        This helper method decodes the subject using the email.header module,
        falling back to UTF-8 if no encoding is specified, and replaces any
        decoding errors.

        Args:
            subject (str): The raw subject string from the email.

        Returns:
            str: The decoded subject string.
        """

        if not subject:
            return ""

        return "".join(
            (
                fragment.decode(encoding or "utf-8", errors="replace")
                if isinstance(fragment, bytes)
                else fragment
            )
            for fragment, encoding in decode_header(subject)
        )
