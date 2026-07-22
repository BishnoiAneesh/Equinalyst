"""Shared declarative mixins used across all ORM models.

Keeping the UUID primary key pattern and timestamp columns in one place avoids
repeating the same `mapped_column(...)` boilerplate on every model (DRY / SOLID
single-responsibility for "how a row identifies and timestamps itself").
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key generated server-side... no, client-side via uuid4.

    Using Python-side `default=uuid.uuid4` (not a DB default) keeps the ID
    available immediately after `session.add()`, before flush — useful when a
    caller needs the new PK to enqueue a Celery task in the same request.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class CreatedAtMixin:
    """Adds a server-side `created_at` timestamp (set once, never mutated)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
