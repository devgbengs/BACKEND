"""update inventory transaction type enum to uppercase

Revision ID: ede2b1980c90
Revises: 4ecd32a179a0
Create Date: 2025-09-26 15:52:55.124727

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ede2b1980c90'
down_revision: Union[str, None] = '4ecd32a179a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a new enum type with updated values
    op.execute("ALTER TYPE inventorytransactiontype RENAME TO inventorytransactiontype_old")
    op.execute("CREATE TYPE inventorytransactiontype AS ENUM ('STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT', 'TRANSFER')")
    
    # Convert existing column data to use new enum type
    op.execute("""
        ALTER TABLE inventory_transactions 
        ALTER COLUMN transaction_type TYPE inventorytransactiontype 
        USING transaction_type::text::inventorytransactiontype
    """)
    
    # Drop the old enum type
    op.execute("DROP TYPE inventorytransactiontype_old")


def downgrade() -> None:
    # Create old enum type
    op.execute("ALTER TYPE inventorytransactiontype RENAME TO inventorytransactiontype_new")
    op.execute("CREATE TYPE inventorytransactiontype AS ENUM ('stock_in', 'stock_out', 'adjustment', 'transfer')")
    
    # Convert existing column data to use old enum type
    op.execute("""
        ALTER TABLE inventory_transactions 
        ALTER COLUMN transaction_type TYPE inventorytransactiontype 
        USING transaction_type::text::inventorytransactiontype
    """)
    
    # Drop the new enum type
    op.execute("DROP TYPE inventorytransactiontype_new")
