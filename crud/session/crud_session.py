from datetime import datetime
from typing import Optional
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from model.models import UserSession
from schema.session import SessionCreate, SessionUpdate
from ..base import CRUDBase

class CRUDSession(CRUDBase[UserSession, SessionCreate, SessionUpdate]):
    async def get_by_refresh_token(
        self,
        db: Session,
        *,
        refresh_token: str
    ) -> Optional[UserSession]:
        """Get a session by refresh token"""
        statement = (
            select(UserSession)
            .where(UserSession.refresh_token == refresh_token)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create_session(
        self,
        db: Session,
        *,
        user_id: int,
        refresh_token: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserSession:
        """Create a new user session"""
        db_obj = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def invalidate_session(
        self,
        db: Session,
        *,
        refresh_token: str
    ) -> bool:
        """Invalidate a session by its refresh token"""
        session = await self.get_by_refresh_token(db, refresh_token=refresh_token)
        if not session:
            return False
        
        session.is_valid = False
        session.invalidated_at = datetime.utcnow()
        db.add(session)
        await db.commit()
        return True

session = CRUDSession(UserSession)
