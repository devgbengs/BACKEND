"""add_token_to_user_sessions

Revision ID: add_token_to_user_sessions_v2
Revises: 
Create Date: 2025-10-08

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_token_to_user_sessions_v2'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add token column to user_sessions table
    op.add_column('user_sessions', sa.Column('token', sa.String(length=512), nullable=True))
    op.create_index(op.f('ix_user_sessions_token'), 'user_sessions', ['token'], unique=True)

def downgrade():
    # Remove token column
    op.drop_index(op.f('ix_user_sessions_token'), table_name='user_sessions')
    op.drop_column('user_sessions', 'token')