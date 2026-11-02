"""Shared input validation constants and helpers.

Responsibilities:

- Allowed values for attendance statuses and user roles
  (``VALID_STATUSES``, ``VALID_ROLES``).
- Password policy constant (``MIN_PASSWORD_LENGTH``) and the encodability
  check applied before hashing (``_is_encodable``).
- Normalisation of attendance status strings (``normalize_status``) and
  ``YYYY-MM-DD`` date strings (``parse_date``).

These are pure functions with no Flask, request, or database dependencies.
``app.routes`` re-exports every name defined here for backward compatibility.
"""

from datetime import datetime

VALID_STATUSES = {"Present", "Absent", "Late"}
VALID_ROLES = {"admin", "teacher", "student"}
MIN_PASSWORD_LENGTH = 8


def normalize_status(status):
    """Normalize and validate attendance status."""
    if not isinstance(status, str):
        return None
    cleaned = status.strip().capitalize()
    if cleaned in VALID_STATUSES:
        return cleaned
    return None


def parse_date(date_str):
    """Parse and validate date string formatted as YYYY-MM-DD."""
    if not isinstance(date_str, str):
        return None
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def _is_encodable(text):
    """Reject strings the password hasher cannot encode (lone surrogates)."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True
