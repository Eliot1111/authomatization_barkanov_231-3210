"""Add UserActivityLog table

Revision ID: 002_user_activity_log
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = '002_user_activity_log'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Проверяем, существует ли таблица (на случай, если она уже создана через Base.metadata.create_all)
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names(schema='lib')
    
    if 'user_activity_log' not in tables:
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
    else:
        # Таблица уже существует (создана через Base.metadata.create_all)
        # Проверяем и создаем индексы, если их нет
        try:
            indexes = [idx['name'] for idx in inspector.get_indexes('user_activity_log', schema='lib')]
        except Exception:
            indexes = []
        
        # Проверяем наличие индексов через SQL запрос
        index_query = text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'lib' 
            AND tablename = 'user_activity_log'
        """)
        existing_indexes = [row[0] for row in conn.execute(index_query)]
        
        if 'ix_user_activity_log_user_id' not in existing_indexes:
            try:
                op.create_index(
                    'ix_user_activity_log_user_id',
                    'user_activity_log',
                    ['user_id'],
                    schema='lib'
                )
            except Exception as e:
                print(f"Warning: Could not create index ix_user_activity_log_user_id: {e}")
        
        if 'ix_user_activity_log_created_at' not in existing_indexes:
            try:
                op.create_index(
                    'ix_user_activity_log_created_at',
                    'user_activity_log',
                    ['created_at'],
                    schema='lib'
                )
            except Exception as e:
                print(f"Warning: Could not create index ix_user_activity_log_created_at: {e}")
        
        print("Table user_activity_log already exists, skipping creation. Indexes checked/created.")


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index('ix_user_activity_log_created_at', table_name='user_activity_log', schema='lib')
    op.drop_index('ix_user_activity_log_user_id', table_name='user_activity_log', schema='lib')
    
    # Удаляем таблицу
    op.drop_table('user_activity_log', schema='lib')

