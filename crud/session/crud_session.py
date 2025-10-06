from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from crud.base import CRUDBase
from model.models import Session
from schema.session import SessionCreate, SessionUpdate
from core.config import settings

class CRUDSession(CRUDBase[Session, SessionCreate, SessionUpdate]):
    async def create_session(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        token: str,
        expires_at: Optional[datetime] = None
    ) -> Session:
        """Create a new session for a user"""
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Deactivate any existing active sessions for this user
        await self.deactivate_user_sessions(db, user_id=user_id)

        # Create new session
        session = Session(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            is_active=True
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_active_session(
        self,
        db: AsyncSession,
        *,
        token: str
    ) -> Optional[Session]:
        """Get an active session by token"""
        query = select(Session).where(
            and_(
                Session.token == token,
                Session.is_active == True,
                Session.expires_at > datetime.utcnow()
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def deactivate_user_sessions(
        self,
        db: AsyncSession,
        *,
        user_id: int
    ) -> None:
        """Deactivate all active sessions for a user"""
        query = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.is_active == True
            )
        )
        result = await db.execute(query)
        sessions = result.scalars().all()

        for session in sessions:
            session.is_active = False
            db.add(session)

        await db.commit()

    async def invalidate_session(
        self,
        db: AsyncSession,
        *,
        token: str
    ) -> Optional[Session]:
        """Invalidate a specific session"""
        session = await self.get_active_session(db, token=token)
        if session:
            session.is_active = False
            db.add(session)
            await db.commit()
            await db.refresh(session)
        return session

session = CRUDSession(Session)