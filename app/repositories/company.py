from __future__ import annotations

from sqlalchemy import select

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    model = Company

    async def get_by_ticker(self, ticker: str) -> Company | None:
        stmt = select(Company).where(Company.ticker == ticker.upper())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_ticker(self, ticker: str) -> bool:
        return await self.get_by_ticker(ticker) is not None
