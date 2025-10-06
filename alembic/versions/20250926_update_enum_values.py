"""update inventory transaction type values

Revision ID: 20250926_update_enum_values
Revises: ede2b1980c90
Create Date: 2025-09-26 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20250926_update_enum_values'
down_revision: Union[str, None] = 'ede2b1980c90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Update existing enum values by temporarily changing the type to text and back
    with op.get_context().autocommit_block():
        op.execute("ALTER TABLE inventory_transactions ALTER COLUMN transaction_type TYPE text")
        op.execute("DROP TYPE inventorytransactiontype")
        op.execute("CREATE TYPE inventorytransactiontype AS ENUM ('STOCK_IN', 'STOCK_OUT', 'ADJUSTMENT', 'TRANSFER')")
        op.execute("ALTER TABLE inventory_transactions ALTER COLUMN transaction_type TYPE inventorytransactiontype USING transaction_type::inventorytransactiontype")