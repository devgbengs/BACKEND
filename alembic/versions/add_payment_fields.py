"""add payment fields to orders

Revision ID: add_payment_fields
Revises: 
Create Date: 2025-10-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_payment_fields'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add payment-related columns to orders table
    op.add_column('orders', sa.Column('payment_status', postgresql.ENUM('UNPAID', 'PARTIALLY_PAID', 'PAID', 'REFUNDED', name='payment_status_enum'), nullable=False, server_default='UNPAID'))
    op.add_column('orders', sa.Column('payment_method', postgresql.ENUM('CASH', 'CARD', 'TRANSFER', 'CREDIT', name='payment_method_enum'), nullable=True))
    op.add_column('orders', sa.Column('subtotal', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('orders', sa.Column('tax_amount', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('orders', sa.Column('notes', sa.String(), nullable=True))
    
    # Create indices for new columns
    op.create_index(op.f('ix_orders_payment_status'), 'orders', ['payment_status'])

def downgrade():
    # Remove indices
    op.drop_index(op.f('ix_orders_payment_status'))
    
    # Remove columns
    op.drop_column('orders', 'notes')
    op.drop_column('orders', 'tax_amount')
    op.drop_column('orders', 'subtotal')
    op.drop_column('orders', 'payment_method')
    op.drop_column('orders', 'payment_status')
    
    # Drop enums
    op.execute('DROP TYPE payment_status_enum')
    op.execute('DROP TYPE payment_method_enum')