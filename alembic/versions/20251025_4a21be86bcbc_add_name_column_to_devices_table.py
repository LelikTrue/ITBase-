"""Add name column to devices table

Revision ID: 4a21be86bcbc
Revises: 8fc178ad1a1b
Create Date: 2025-10-25 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "4a21be86bcbc"
down_revision = "8fc178ad1a1b"  # Замени на ID твоей предыдущей миграции
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Шаг 1: Добавляем колонку, временно разрешая NULL ###
    op.add_column("devices", sa.Column("name", sa.String(length=255), nullable=True))

    # ### Шаг 2: Заполняем существующие строки значением по умолчанию ###
    # Мы будем использовать инвентарный номер в качестве временного названия.
    op.execute("UPDATE devices SET name = inventory_number WHERE name IS NULL")

    # ### Шаг 3: Устанавливаем для колонки ограничение NOT NULL ###
    op.alter_column("devices", "name", nullable=False)


def downgrade() -> None:
    # ### При откате просто удаляем колонку ###
    op.drop_column("devices", "name")
