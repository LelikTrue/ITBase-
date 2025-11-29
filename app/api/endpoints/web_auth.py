# app/api/endpoints/web_auth.py
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.db.database import get_db
from app.flash import flash
from app.models.user import User
from app.templating import templates

router = APIRouter()


@router.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page"""
    # If user is already logged in, redirect to dashboard
    if request.session.get('user_email'):
        return RedirectResponse(url='/dashboard', status_code=303)

    return templates.TemplateResponse('login.html', {'request': request})


@router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    """Display registration page"""
    # If user is already logged in, redirect to dashboard
    if request.session.get('user_email'):
        return RedirectResponse(url='/dashboard', status_code=303)

    return templates.TemplateResponse('register.html', {'request': request})


@router.post('/register')
async def register_user(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password_confirm: Annotated[str, Form()],
    full_name: Annotated[str, Form()] = '',
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Process registration form and create new user"""
    # Validate passwords match
    if password != password_confirm:
        flash(request, 'Пароли не совпадают', category='danger')
        return RedirectResponse(url='/register', status_code=303)

    # Validate password length
    if len(password) < 8:
        flash(request, 'Пароль должен содержать минимум 8 символов', category='danger')
        return RedirectResponse(url='/register', status_code=303)

    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == email))
    existing_user = result.scalars().first()

    if existing_user:
        flash(request, 'Пользователь с таким email уже существует', category='danger')
        return RedirectResponse(url='/register', status_code=303)

    # Create new user
    hashed_password = security.get_password_hash(password)
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name if full_name else None,
        is_active=True,
        is_superuser=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Auto-login after registration
    request.session['user_id'] = new_user.id
    request.session['user_email'] = new_user.email
    request.session['user_name'] = new_user.full_name or new_user.email
    request.session['is_superuser'] = new_user.is_superuser

    flash(
        request,
        f'Добро пожаловать, {new_user.full_name or new_user.email}! Регистрация прошла успешно.',
        category='success',
    )
    return RedirectResponse(url='/dashboard', status_code=303)


@router.post('/login')
async def web_login(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Process login form and create session"""
    # Authenticate user
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()

    if not user or not security.verify_password(password, user.hashed_password):
        flash(request, 'Неверный email или пароль', category='danger')
        return RedirectResponse(url='/login', status_code=303)

    if not user.is_active:
        flash(request, 'Ваш аккаунт деактивирован', category='warning')
        return RedirectResponse(url='/login', status_code=303)

    # Create session
    request.session['user_id'] = user.id
    request.session['user_email'] = user.email
    request.session['user_name'] = user.full_name or user.email
    request.session['is_superuser'] = user.is_superuser

    flash(
        request,
        f'Добро пожаловать, {user.full_name or user.email}!',
        category='success',
    )
    return RedirectResponse(url='/dashboard', status_code=303)


@router.get('/logout')
async def web_logout(request: Request):
    """Clear session and redirect to login"""
    request.session.clear()
    flash(request, 'Вы вышли из системы', category='info')
    return RedirectResponse(url='/login', status_code=303)
