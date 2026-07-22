from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.models.valuation_version import ValuationVersion
from app.repositories.base import BaseRepository


class ValuationVersionRepository(BaseRepository[ValuationVersion]):
    model = ValuationVersion

    async def list_for_company(
        self, company_id: uuid.UUID, *, limit: int = 50, offset: int = 0
    ) -> list[ValuationVersion]:
        """Paginated versions, newest first — backs GET .../valuations/versions (Sprint 4)."""
        stmt = (
            select(ValuationVersion)
            .where(ValuationVersion.company_id == company_id)
            .order_by(ValuationVersion.version_number.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_company_and_version_number(
        self, company_id: uuid.UUID, version_number: int
    ) -> ValuationVersion | None:
        stmt = select(ValuationVersion).where(
            ValuationVersion.company_id == company_id,
            ValuationVersion.version_number == version_number,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def next_version_number(self, company_id: uuid.UUID) -> int:
        """Compute the next version_number for a company.

        NOTE: this alone is not concurrency-safe. Sprint 4's
        VersioningService.save_version wraps the read+insert in a
        `SELECT ... FOR UPDATE` on a per-company lock row (or an advisory
        lock) as specified in the roadmap, to avoid two concurrent valuation
        requests computing the same next version_number.
        """
        stmt = select(func.max(ValuationVersion.version_number)).where(
            ValuationVersion.company_id == company_id
        )
        result = await self.session.execute(stmt)
        current_max = result.scalar()
        return (current_max or 0) + 1
