"""Company — the root entity every other domain table hangs off.

A row is created the moment a user asks to ingest a ticker (Sprint 3,
POST /api/v1/companies) and is never re-created for the same ticker afterwards;
re-ingestion just adds new FinancialSnapshot rows.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.financial_snapshot import FinancialSnapshot
    from app.models.valuation_version import ValuationVersion


class Company(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """An NSE/BSE-listed company tracked by the platform."""

    __tablename__ = "companies"

    ticker: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)  # "NSE" | "BSE"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Canonical Screener.in company URL, e.g. https://www.screener.in/company/RELIANCE/
    screener_url: Mapped[str] = mapped_column(String(512), nullable=False)

    # System_Architecture.txt, Module 1: ingestion always prefers the
    # consolidated tab and falls back to standalone if it's absent.
    use_consolidated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Sprint 5 adds a FK here to scope companies to the user who created them.
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    financial_snapshots: Mapped[list[FinancialSnapshot]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    valuation_versions: Mapped[list[ValuationVersion]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<Company {self.ticker} ({self.exchange})>"
