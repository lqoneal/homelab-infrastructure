"""Engineering Event & Notification System."""

from .events import EngineeringEvent, EventValidationError
from .store import (
    AppendResult,
    EventStore,
    IdempotencyConflictError,
    StoredEvent,
)

__all__ = [
    "AppendResult",
    "EngineeringEvent",
    "EventStore",
    "EventValidationError",
    "IdempotencyConflictError",
    "StoredEvent",
]

__version__ = "0.1.0-alpha"
