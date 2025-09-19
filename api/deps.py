from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from core.database import get_async_session
from model.models import User
from schema.token import TokenData
from crud.user.crud_user import user

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token",
    scheme_name="JWT",
    description="Enter your access token here"
)

# Define a separate scheme for refresh tokens
refresh_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token",
    scheme_name="JWT-refresh",
    description="Enter your refresh token here (for token refresh only)"
)

async def get_current_user(
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(sub=user_id, exp=payload.get("exp"))
        
        # Convert user_id to int since it comes as string from JWT
        user_id_int = int(user_id)
        db_user = await user.get(db, id=user_id_int)
        
        if db_user is None:
            raise credentials_exception
            
        return db_user
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid user ID format: {ve}"
        )
    except JWTError as je:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"JWT validation failed: {je}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )

async def get_current_refresh_user(
    db: AsyncSession = Depends(get_async_session),
    token: str = Depends(refresh_oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # Explicitly check for refresh token type
        token_type = payload.get("type")
        if not token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token type not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Please use a refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(sub=user_id, exp=payload.get("exp"))
    except JWTError:
        raise credentials_exception
    
    db_user = await user.get(db, id=token_data.sub)
    if db_user is None:
        raise credentials_exception
    return db_user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not "admin" in current_user.role_names:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user