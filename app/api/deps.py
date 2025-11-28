# app/api/deps.py
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import TokenData

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/login/access-token")


async def get_current_user(
    token: Annotated[str, Depends(reusable_oauth2)],
    db: Annotated[AsyncSession, Depends(get_db)],
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
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except (JWTError, ValidationError):
        raise credentials_exception

    result = await db.execute(select(User).filter(User.email == token_data.email))
    user = result.scalars().first()

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Get current active superuser (combines active and superuser checks)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


# --- Session-based authentication for web routes ---


async def get_current_user_from_session(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Get current user from session (for web routes)"""
    user_id = request.session.get("user_id")

    if not user_id:
        # Redirect to login page
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Not authenticated",
            headers={"Location": "/login"},
        )

    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()

    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="User not found",
            headers={"Location": "/login"},
        )

    return user


async def get_current_superuser_from_session(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user_from_session)],
) -> User:
    """Get current superuser from session (for web routes)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
