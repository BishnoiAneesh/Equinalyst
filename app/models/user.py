"""User and RefreshToken — schema now, wired up to auth logic in Sprint 5.

Creating these tables in Sprint 2 (rather than deferring to Sprint 5) lets
`valuation_versions.created_by` and `export_jobs.user_id` declare real foreign
keys from day one instead of bolting them on with a later migration.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    """One row per issued refresh token, enabling rotation and revocation.

    Storing the token itself (hashed, in Sprint 5) rather than trusting a
    stateless JWT alone is what makes rotation and "log out everywhere"
    possible per the Sprint 5 auth-hardening plan.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RefreshToken user={self.user_id} revoked={self.revoked}>"
