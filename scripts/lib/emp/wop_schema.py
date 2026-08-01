"""Canonical rules shared by WOP submission and execution validation."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any


# Published Beta WOPs use semantic identities (for example,
# WOP-ZDCL-01-FOUNDATION-001). UUID identities remain accepted for legacy
# standalone packages and historical records.
SEMANTIC_WOP_ID = re.compile(r"^WOP-[A-Z0-9]+(?:-[A-Z0-9.]+)+$")
UUID_WOP_ID = re.compile(
    r"^WOP-[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def is_wop_id(value: Any) -> bool:
    """Return whether *value* is a canonical semantic or legacy UUID WOP ID."""
    return isinstance(value, str) and bool(
        SEMANTIC_WOP_ID.fullmatch(value) or UUID_WOP_ID.fullmatch(value)
    )


def validate_optional_approval_date(value: Any) -> bool:
    """Approval date is optional; when present it must be ISO-8601."""
    if value in (None, ""):
        return True
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True
