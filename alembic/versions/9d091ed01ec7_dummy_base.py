"""dummy base migration

Revision ID: 9d091ed01ec7
Revises: 
Create Date: 2025-07-15 14:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d091ed01ec7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This was a phantom migration, do nothing.
    pass


def downgrade() -> None:
    # This was a phantom migration, do nothing.
    pass
