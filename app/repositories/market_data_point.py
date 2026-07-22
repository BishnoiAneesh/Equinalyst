from __future__ import annotations

from sqlalchemy import select

from app.models.market_data_point import MarketDataPoint
from app.repositories.base import BaseRepository


class MarketDataPointRepository(BaseRepository[MarketDataPoint]):
    model = MarketDataPoint

    async def get_latest_for_ticker(self, ticker: str) -> MarketDataPoint | None:
        """Most recent price/ratio reading for a ticker.

        Backed by the (ticker, fetched_at) index declared on the model —
        this is the exact access pattern that index exists for.
        """
        stmt = (
            select(MarketDataPoint)
            .where(MarketDataPoint.ticker == ticker.upper())
            .order_by(MarketDataPoint.fetched_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_history_for_ticker(
        self, ticker: str, *, limit: int = 100
    ) -> list[MarketDataPoint]:
        stmt = (
            select(MarketDataPoint)
            .where(MarketDataPoint.ticker == ticker.upper())
            .order_by(MarketDataPoint.fetched_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
