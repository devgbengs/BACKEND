"""empty message

Revision ID: b622d210055b
Revises: 7f80e0d60341, dc6eed0eb911
Create Date: 2025-09-18 20:01:19.123248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b622d210055b'
down_revision: Union[str, None] = ('7f80e0d60341', 'dc6eed0eb911')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
