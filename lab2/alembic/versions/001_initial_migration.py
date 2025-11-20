"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Эта миграция создает базовую структуру БД
    # В реальном проекте здесь были бы все существующие таблицы
    # Для демонстрации оставляем пустым, так как таблицы уже созданы через Base.metadata.create_all
    pass


def downgrade() -> None:
    pass

