from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select

from app.models.user import RefreshToken, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        return await self.get_by_email(email) is not None


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    async def get_active_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > datetime.utcnow(),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Used by a future 'log out everywhere' flow (Sprint 5)."""
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)
        )
        result = await self.session.execute(stmt)
        for token in result.scalars().all():
            token.revoked = True
        await self.session.flush()
