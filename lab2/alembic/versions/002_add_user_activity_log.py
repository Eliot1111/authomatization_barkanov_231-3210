"""Add UserActivityLog table

Revision ID: 002_user_activity_log
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_user_activity_log'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем таблицу user_activity_log в схеме lib
    op.create_table(
        'user_activity_log',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('resource_type', sa.Text(), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('additional_data', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['lib.users.id'], ondelete='CASCADE'),
        schema='lib'
    )
    op.create_primary_key('pk_user_activity_log', 'user_activity_log', ['id'], schema='lib')
    
    # Создаем индекс для быстрого поиска по user_id
    op.create_index(
        'ix_user_activity_log_user_id',
        'user_activity_log',
        ['user_id'],
        schema='lib'
    )
    
    # Создаем индекс для быстрого поиска по дате
    op.create_index(
        'ix_user_activity_log_created_at',
        'user_activity_log',
        ['created_at'],
        schema='lib'
    )


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index('ix_user_activity_log_created_at', table_name='user_activity_log', schema='lib')
    op.drop_index('ix_user_activity_log_user_id', table_name='user_activity_log', schema='lib')
    
    # Удаляем таблицу
    op.drop_table('user_activity_log', schema='lib')

