"""Generic async repository base.

Every domain repository below extends this instead of re-implementing
get/list/add/delete. This is the DRY layer the task list calls for
("repository classes with typed async CRUD methods") without resorting to a
god-object DAO — each subclass still owns its table-specific query methods.
"""

from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Typed async CRUD primitives shared by every repository.

    Callers own transaction boundaries (commit/rollback) — this class only
    ever flushes, never commits, so it composes cleanly inside a larger
    unit-of-work (e.g. VersioningService.save_version's SELECT FOR UPDATE
    pattern in Sprint 4).
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, id_: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model, id_)

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[ModelT]:
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)

    async def flush(self) -> None:
        await self.session.flush()
