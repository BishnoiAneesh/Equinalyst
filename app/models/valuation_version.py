"""ValuationVersion — the immutable audit record described in Module 3.

No column here is ever UPDATEd after insert (see VersioningService in
Sprint 4); a "revert" creates a brand new version pre-populated from an old
one's inputs_snapshot rather than mutating history.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company


class ValuationVersion(UUIDPrimaryKeyMixin, Base):
    """A single immutable, versioned DCF (or other model) run for a company."""

    __tablename__ = "valuation_versions"
    __table_args__ = (
        UniqueConstraint("company_id", "version_number", name="uq_valuation_version_company_num"),
    )

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    model: Mapped[str] = mapped_column(String(32), nullable=False)  # "dcf" | "ddm" | ...

    # Full ValuationRequest.assumptions copy, append-only, never mutated.
    inputs_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # Full ValuationResult copy, append-only, never mutated.
    result_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Sprint 5 adds the FK to users.id once auth lands; nullable now so this
    # table is usable (e.g. from scripts/seed.py) before auth exists.
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    company: Mapped[Company] = relationship(back_populates="valuation_versions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ValuationVersion company={self.company_id} v{self.version_number}>"
