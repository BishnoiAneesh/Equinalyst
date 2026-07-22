"""MarketDataPoint — point-in-time price/ratio snapshot scraped from Screener.in.

Not FK'd to Company on purpose: it's keyed by ticker like Screener itself, so
the ingestion writer can insert a row before a Company record necessarily
exists in edge cases (e.g. a bulk refresh keyed only by ticker list).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class MarketDataPoint(UUIDPrimaryKeyMixin, Base):
    """A single scraped price/ratio reading for a ticker, sourced from Screener.in."""

    __tablename__ = "market_data_points"
    __table_args__ = (
        # System_Architecture.txt Module 1: "add index on (ticker, fetched_at DESC)"
        # — this is the access pattern for "latest price for ticker X".
        Index("ix_market_data_points_ticker_fetched_at", "ticker", "fetched_at"),
    )

    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False)  # "NSE" | "BSE"

    price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)  # INR
    market_cap: Mapped[float | None] = mapped_column(Numeric(20, 2), nullable=True)  # INR Cr
    pe_ratio: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    book_value: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)  # INR/share

    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="screener")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MarketDataPoint {self.ticker} @ {self.fetched_at}>"
