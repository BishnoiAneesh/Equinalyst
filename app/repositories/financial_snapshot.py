from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.financial_snapshot import FinancialSnapshot
from app.repositories.base import BaseRepository


class FinancialSnapshotRepository(BaseRepository[FinancialSnapshot]):
    model = FinancialSnapshot

    async def list_for_company(
        self, company_id: uuid.UUID, *, order_desc: bool = True
    ) -> list[FinancialSnapshot]:
        """Return snapshots for a company ordered by fiscal period.

        Used by GET /api/v1/companies/{id}/financials (Sprint 3) which the
        roadmap specifies must return snapshots "ordered by period desc".
        """
        stmt = select(FinancialSnapshot).where(FinancialSnapshot.company_id == company_id)
        stmt = stmt.order_by(
            FinancialSnapshot.period.desc() if order_desc else FinancialSnapshot.period.asc()
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_company_and_period(
        self, company_id: uuid.UUID, period: str
    ) -> FinancialSnapshot | None:
        stmt = select(FinancialSnapshot).where(
            FinancialSnapshot.company_id == company_id,
            FinancialSnapshot.period == period,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, **fields: Any) -> FinancialSnapshot:
        """Insert a snapshot, or update it in place if (company_id, period) already exists.

        This is the "ingestion writer service" upsert behaviour called for in
        Sprint 3 task 7 — re-ingesting a ticker must not create duplicate rows
        per fiscal year. Uses Postgres' native ON CONFLICT so the upsert is
        atomic rather than a racy get-then-insert.
        """
        insert_stmt = pg_insert(FinancialSnapshot).values(**fields)
        stmt = (
            insert_stmt.on_conflict_do_update(
                constraint="uq_financial_snapshot_company_period",
                set_={
                    "scraped_at": insert_stmt.excluded.scraped_at,
                    "use_consolidated": insert_stmt.excluded.use_consolidated,
                    "raw_html_payload": insert_stmt.excluded.raw_html_payload,
                    "parsed_fields": insert_stmt.excluded.parsed_fields,
                    "ingested_at": insert_stmt.excluded.ingested_at,
                },
            )
            .returning(FinancialSnapshot)
            # On the update path, this row's PK is already in the session's
            # identity map from the earlier insert. Without populate_existing,
            # SQLAlchemy returns that cached (stale) instance instead of
            # applying the freshly RETURNING'd column values.
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one()
