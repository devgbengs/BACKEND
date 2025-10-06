"""recreate inventory transactions table

Revision ID: 20250926_recreate_inventory_table
Revises: ede2b1980c90
Create Date: 2025-09-26 17:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250926_recreate_inventory_table'
down_revision: Union[str, None] = 'ede2b1980c90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Drop existing table and enum if they exist
    op.execute("DROP TABLE IF EXISTS inventory_transactions CASCADE")
    op.execute("DROP TYPE IF EXISTS inventorytransactiontype CASCADE")
    
    # Create enum type
    op.execute("CREATE TYPE inventorytransactiontype AS ENUM ('STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT', 'TRANSFER')")
    
    # Create table
    op.create_table('inventory_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('reference_number', sa.String(), nullable=False),
        sa.Column('transaction_type', postgresql.ENUM('STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT', 'TRANSFER', name='inventorytransactiontype'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('previous_quantity', sa.Integer(), nullable=False),
        sa.Column('new_quantity', sa.Integer(), nullable=False),
        sa.Column('transaction_date', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reference_number')
    )
    op.create_index(op.f('ix_inventory_transactions_tenant_id'), 'inventory_transactions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_product_id'), 'inventory_transactions', ['product_id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_warehouse_id'), 'inventory_transactions', ['warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_transaction_type'), 'inventory_transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_reference_number'), 'inventory_transactions', ['reference_number'], unique=True)

def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_transactions_warehouse_id'), table_name='inventory_transactions')
    op.drop_index(op.f('ix_inventory_transactions_transaction_type'), table_name='inventory_transactions')
    op.drop_index(op.f('ix_inventory_transactions_tenant_id'), table_name='inventory_transactions')
    op.drop_index(op.f('ix_inventory_transactions_reference_number'), table_name='inventory_transactions')
    op.drop_index(op.f('ix_inventory_transactions_product_id'), table_name='inventory_transactions')
    op.drop_table('inventory_transactions')
    op.execute("DROP TYPE inventorytransactiontype")