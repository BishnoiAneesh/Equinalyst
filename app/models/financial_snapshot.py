"""FinancialSnapshot — one row per (company, fiscal year), per System_Architecture.txt Module 1.

`raw_html_payload` is kept even though it duplicates data already reflected in
`parsed_fields`: it is the re-parse safety net described in the architecture
doc ("if field_map.py is updated to handle a Screener layout change,
historical data can be re-parsed from the stored HTML without re-fetching").
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company


class FinancialSnapshot(UUIDPrimaryKeyMixin, Base):
    """A single fiscal year's parsed financials scraped from Screener.in."""

    __tablename__ = "financial_snapshots"
    __table_args__ = (
        # A company can only have one snapshot per fiscal period; re-ingestion
        # upserts this row rather than duplicating it (Sprint 3 writer service).
        UniqueConstraint("company_id", "period", name="uq_financial_snapshot_company_period"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Denormalised on purpose: lets analytics/export queries filter by ticker
    # without a join, and survives even if the company row is ever repointed.
    ticker: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    period: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. "FY2024"

    use_consolidated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Full page HTML, preserved verbatim for re-parsing (see module docstring).
    raw_html_payload: Mapped[str] = mapped_column(Text, nullable=False)

    # Normalised field name -> value (INR Cr for company-level figures), keyed
    # per app/ingestion/field_map.py (Sprint 3).
    parsed_fields: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    company: Mapped[Company] = relationship(back_populates="financial_snapshots")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FinancialSnapshot {self.ticker} {self.period}>"
