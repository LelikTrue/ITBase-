# create_admin.py
"""Script to create a superuser admin account"""

import asyncio
import getpass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core import security
from app.models.user import User


async def create_superuser():
    """Create a superuser interactively"""
    print('=== Создание администратора ===\n')

    # Get user input
    email = input('Email: ').strip()
    if not email:
        print('❌ Email обязателен!')
        return

    full_name = input('Полное имя (опционально): ').strip() or None

    password = getpass.getpass('Пароль: ')
    password_confirm = getpass.getpass('Подтвердите пароль: ')

    if password != password_confirm:
        print('❌ Пароли не совпадают!')
        return

    if len(password) < 6:
        print('❌ Пароль должен быть минимум 6 символов!')
        return

    # Create database engine
    engine = create_async_engine(settings.DATABASE_URL_ASYNC, echo=False)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if user already exists
        result = await session.execute(select(User).filter(User.email == email))
        existing_user = result.scalars().first()

        if existing_user:
            print(f'❌ Пользователь с email {email} уже существует!')
            return

        # Create superuser
        user = User(
            email=email,
            hashed_password=security.get_password_hash(password),
            full_name=full_name,
            is_active=True,
            is_superuser=True,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        print('\n✅ Администратор успешно создан!')
        print(f'   ID: {user.id}')
        print(f'   Email: {user.email}')
        print(f"   Имя: {user.full_name or 'Не указано'}")
        print('   Суперпользователь: Да')

    await engine.dispose()


if __name__ == '__main__':
    asyncio.run(create_superuser())
