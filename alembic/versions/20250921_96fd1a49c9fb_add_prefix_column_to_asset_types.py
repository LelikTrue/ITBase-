"""Add prefix column to asset types

Revision ID: 96fd1a49c9fb
Revises: 4631d721d198
Create Date: 2025-09-21 08:58:53.620531

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '96fd1a49c9fb'
down_revision: str | None = '4631d721d198'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### НАЧАЛО НАШИХ ПРАВОК ###

    # Шаг 1: Создаем колонку, но ВРЕМЕННО разрешаем ей быть пустой (nullable=True)
    op.add_column(
        'assettypes', sa.Column('prefix', sa.String(length=10), nullable=True)
    )

    # Шаг 2: Заполняем новую колонку для СУЩЕСТВУЮЩИХ строк.
    # Мы генерируем временный префикс из первых 3 букв имени + ID, чтобы он был уникальным.
    # Например: "Ноутбук" (id=1) -> "НОУ1"
    # Ты сможешь потом поменять их на нормальные через админку.
    op.execute(
        'UPDATE assettypes SET prefix = UPPER(SUBSTRING(name FROM 1 FOR 3)) || id::text'
    )

    # Шаг 3: Теперь, когда все строки заполнены, мы можем сделать колонку ОБЯЗАТЕЛЬНОЙ.
    op.alter_column('assettypes', 'prefix', nullable=False)

    # Шаг 4: Добавляем ограничение уникальности.
    op.create_unique_constraint('uq_assettypes_prefix', 'assettypes', ['prefix'])

    # ### КОНЕЦ НАШИХ ПРАВОК ###


def downgrade() -> None:
    # ### НАЧАЛО НАШИХ ПРАВОК ###

    # Откат происходит в обратном порядке
    op.drop_constraint('uq_assettypes_prefix', 'assettypes', type_='unique')
    op.drop_column('assettypes', 'prefix')

    # ### КОНЕЦ НАШИХ ПРАВОК ###
