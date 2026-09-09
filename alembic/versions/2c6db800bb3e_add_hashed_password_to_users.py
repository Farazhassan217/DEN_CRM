"""add hashed_password to users

Revision ID: 2c6db800bb3e
Revises: 88fe24ac8b12
Create Date: 2026-08-10 15:21:39.408078

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_hashed_password'
down_revision: Union[str, None] = 'initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aapka upgrade code yahan hoga (jaise add column hashed_password etc.)
    pass


def downgrade() -> None:
    # Aapka downgrade code yahan hoga
    pass

def upgrade() -> None:
    # Sirf hashed_password ka column add karna hai
    op.add_column('Users', sa.Column('hashed_password', sa.VARCHAR(length=255), nullable=True))


def downgrade() -> None:
    # Rollback ke liye column drop kar dein
    op.drop_column('Users', 'hashed_password')