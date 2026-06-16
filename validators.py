"""
Server-side validation + typing.

The browser form already guides the user (required fields, live totals), but we
never trust the client: every field is re-parsed and re-validated here before it
touches the database. Returns clean, correctly-typed values plus a list of
human-readable errors.
"""
from __future__ import annotations

import re
from datetime import date

ACCOUNT_CATEGORIES: tuple[str, ...] = ("retirement", "non_retirement", "trust", "liability")
ACCOUNT_OWNERS: tuple[str, ...] = ("client1", "client2", "joint")

MAX_MONEY = 1_000_000_000_000.0   # $1T sanity ceiling
MAX_TEXT = 120


def clean_text(raw: str | None, *, max_len: int = MAX_TEXT) -> str:
    """Trim and length-cap a free-text field (Jinja autoescaping handles XSS)."""
    return (raw or "").strip()[:max_len]


def digits_only(raw: str | None, *, max_len: int) -> str:
    """Keep digits only — used for SSN last-4 and account last-4."""
    return re.sub(r"\D", "", raw or "")[:max_len]


def parse_money(
    raw: str | None,
    *,
    field: str,
    errors: list[str],
    required: bool = False,
    min_value: float = 0.0,
) -> float | None:
    """Parse a currency-ish field. Tolerates '$' and ','. Enforces type & range."""
    s = (raw or "").replace("$", "").replace(",", "").strip()
    if s == "":
        if required:
            errors.append(f"{field} es obligatorio.")
        return None if not required else 0.0
    try:
        value = float(s)
    except ValueError:
        errors.append(f"{field} debe ser un número.")
        return 0.0
    if value < min_value:
        errors.append(f"{field} no puede ser negativo.")
        return min_value
    if value > MAX_MONEY:
        errors.append(f"{field} es demasiado grande.")
        return MAX_MONEY
    return value


def parse_rate(raw: str | None) -> float:
    """Interest rate 0–100, defaults to 0."""
    s = (raw or "").replace("%", "").strip()
    if s == "":
        return 0.0
    try:
        v = float(s)
    except ValueError:
        return 0.0
    return min(max(v, 0.0), 100.0)


def parse_date(raw: str | None, *, field: str, errors: list[str]) -> str | None:
    """Validate an ISO date (YYYY-MM-DD). Blank is allowed. Returns iso or None."""
    s = (raw or "").strip()
    if s == "":
        return None
    try:
        y, m, d = (int(x) for x in s.split("-"))
        parsed = date(y, m, d)
    except (ValueError, AttributeError):
        errors.append(f"{field} no es una fecha válida (use AAAA-MM-DD).")
        return None
    if parsed > date.today():
        errors.append(f"{field} no puede estar en el futuro.")
        return None
    return parsed.isoformat()


def normalize_category(raw: str | None) -> str:
    return raw if raw in ACCOUNT_CATEGORIES else "non_retirement"


def normalize_owner(raw: str | None) -> str:
    return raw if raw in ACCOUNT_OWNERS else "joint"
