from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.export_job import ExportJob
from app.repositories.base import BaseRepository


class ExportJobRepository(BaseRepository[ExportJob]):
    model = ExportJob

    async def list_for_user(self, user_id: uuid.UUID, *, limit: int = 50) -> list[ExportJob]:
        stmt = (
            select(ExportJob)
            .where(ExportJob.user_id == user_id)
            .order_by(ExportJob.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_owned_by_user(self, job_id: uuid.UUID, user_id: uuid.UUID) -> ExportJob | None:
        """Ownership-checked lookup — backs GET /export/download/{job_id} (Sprint 6),
        which must "validate that the requesting user owns the job before serving"."""
        stmt = select(ExportJob).where(ExportJob.id == job_id, ExportJob.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
