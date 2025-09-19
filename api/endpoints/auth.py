from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    verify_password
)
from api.deps import get_async_session, get_current_refresh_user
from crud.user.crud_user import user
from schema.token import Token

router = APIRouter()

@router.post("/login/access-token", response_model=Token, status_code=200)
async def login_access_token(
    db: AsyncSession = Depends(get_async_session),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Get access token for authentication.
    
    ## How to authenticate in Swagger UI:
    1. Click this endpoint (/auth/login/access-token)
    2. Click "Try it out"
    3. Enter credentials:
       - username: test@example.com
       - password: testpassword
    4. Click "Execute"
    5. Copy the access_token value (without quotes)
    6. Click the "Authorize" button at the top of the page
    7. In the authorization popup, enter: Bearer <your_access_token>
       (Replace <your_access_token> with the token you copied)
    8. Click "Authorize" and then "Close"
    
    Now you can use all secured endpoints!
    
    ## Response Format:
    ```json
    {
        "access_token": "eyJhbGc...",
        "refresh_token": "eyJhbGc...",
        "token_type": "bearer"
    }
    ```
    
    ## Important Notes:
    - Use the access_token, not the refresh_token
    - Always include "Bearer " before the token
    - Token expires in 30 minutes
    """
    # Try to authenticate the user
    db_user = await user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not db_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Create access token (for regular API calls)
    access_token = create_access_token(
        subject=str(db_user.id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Create refresh token (only for refresh-token endpoint)
    refresh_token = create_refresh_token(
        subject=str(db_user.id),
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    
    # Return both tokens with clear instructions
    return {
        "access_token": access_token,  # For regular API calls
        "refresh_token": refresh_token,  # For refresh-token endpoint only
        "token_type": "bearer",
        "_note": "To refresh your tokens, use the refresh_token (not access_token) with the /login/refresh-token endpoint"
    }

@router.post("/login/refresh-token", response_model=Token)
async def refresh_token(
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_refresh_user)
) -> Any:
    """
    Refresh access token.
    To use this endpoint:
    1. First login using /login/access-token to get tokens
    2. Use the refresh_token (not access_token) in the Authorization header
    3. The header should be in format: Bearer <refresh_token>
    """
    # Create new access token (for regular API calls)
    access_token = create_access_token(
        subject=str(current_user.id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Create new refresh token (only for refresh-token endpoint)
    refresh_token = create_refresh_token(
        subject=str(current_user.id),
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    
    # Return new tokens with clear instructions
    return {
        "access_token": access_token,  # For regular API calls
        "refresh_token": refresh_token,  # For refresh-token endpoint only
        "token_type": "bearer",
        "_note": "Use the new access_token for API calls. Save the refresh_token for your next refresh."
    }