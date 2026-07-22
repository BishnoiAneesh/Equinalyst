"""ExportJob — tracks async Excel-export jobs against the local export volume.

Per System_Architecture.txt: "This replaces the cloud object storage
reference" — file_path points into the bind-mounted ./data/exports volume,
never a cloud bucket key.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class ExportJobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class ExportJob(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "export_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    valuation_version_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("valuation_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[ExportJobStatus] = mapped_column(
        Enum(ExportJobStatus, name="export_job_status", native_enum=True),
        nullable=False,
        default=ExportJobStatus.PENDING,
    )

    # Local volume path, e.g. /app/data/exports/{user_id}/{version_id}.xlsx
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ExportJob {self.id} status={self.status}>"
