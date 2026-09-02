"""Open (possibly encrypted) PDFs and extract text."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from io import BytesIO
from pathlib import Path


class StatementPasswordError(Exception):
    """PDF is encrypted and the password is missing or wrong."""


@dataclass
class StatementLine:
    date: date | None
    description: str
    amount: float
    kind: str  # purchase | payment | income


@dataclass
class StatementParseResult:
    period_start: date | None = None
    period_end: date | None = None
    previous_balance: float | None = None
    closing_balance: float | None = None
    minimum_payment: float | None = None
    due_date: date | None = None
    lines: list[StatementLine] = field(default_factory=list)
    raw_text: str = ""


def extract_pdf_text(data: bytes, password: str | None = None) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Instala pypdf para leer estados de cuenta") from exc

    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted:
        if not password:
            raise StatementPasswordError("El PDF está cifrado")
        ok = reader.decrypt(password)
        if ok == 0:
            raise StatementPasswordError("Contraseña incorrecta")

    try:
        import pdfplumber
    except ImportError:
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return "\n".join(texts)

    with pdfplumber.open(BytesIO(data), password=password or "") as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def save_pdf(data: bytes, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest
