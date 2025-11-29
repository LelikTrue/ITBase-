# app/api/endpoints/users.py
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core import security
from app.db.database import get_db
from app.flash import flash
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.templating import templates

router = APIRouter()


@router.post('/', response_model=UserResponse)
async def create_user(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_in: UserCreate,
    # current_user: Annotated[User, Depends(deps.get_current_superuser)], # Uncomment to restrict to superusers
) -> Any:
    """
    Create new user.
    """
    result = await db.execute(select(User).filter(User.email == user_in.email))
    user = result.scalars().first()
    if user:
        raise HTTPException(
            status_code=400,
            detail='The user with this username already exists in the system.',
        )

    user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        is_superuser=user_in.is_superuser,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get('/me', response_model=UserResponse)
async def read_user_me(
    current_user: Annotated[User, Depends(deps.get_current_active_user)],
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.get('/admin/users', response_class=HTMLResponse)
async def users_list(
    request: Request,
    current_user: Annotated[User, Depends(deps.get_current_superuser_from_session)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Display list of all users (admin only)"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    return templates.TemplateResponse(
        'admin/users.html',
        {
            'request': request,
            'users': users,
            'current_user_id': current_user.id,
        },
    )


@router.post('/admin/users/{user_id}/toggle-superuser')
async def toggle_superuser(
    request: Request,
    user_id: int,
    current_user: Annotated[User, Depends(deps.get_current_superuser_from_session)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Toggle superuser status for a user (admin only)"""
    if user_id == current_user.id:
        flash(
            request, 'Вы не можете изменить свои собственные права', category='warning'
        )
        return RedirectResponse(url='/admin/users', status_code=303)

    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()

    if not user:
        flash(request, 'Пользователь не найден', category='danger')
        return RedirectResponse(url='/admin/users', status_code=303)

    user.is_superuser = not user.is_superuser
    await db.commit()

    status = 'администратором' if user.is_superuser else 'обычным пользователем'
    flash(request, f'Пользователь {user.email} теперь {status}', category='success')
    return RedirectResponse(url='/admin/users', status_code=303)


@router.post('/admin/users/{user_id}/toggle-active')
async def toggle_active(
    request: Request,
    user_id: int,
    current_user: Annotated[User, Depends(deps.get_current_superuser_from_session)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Toggle active status for a user (admin only)"""
    if user_id == current_user.id:
        flash(
            request,
            'Вы не можете деактивировать свой собственный аккаунт',
            category='warning',
        )
        return RedirectResponse(url='/admin/users', status_code=303)

    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()

    if not user:
        flash(request, 'Пользователь не найден', category='danger')
        return RedirectResponse(url='/admin/users', status_code=303)

    user.is_active = not user.is_active
    await db.commit()

    status = 'активирован' if user.is_active else 'деактивирован'
    flash(request, f'Пользователь {user.email} {status}', category='success')
    return RedirectResponse(url='/admin/users', status_code=303)
