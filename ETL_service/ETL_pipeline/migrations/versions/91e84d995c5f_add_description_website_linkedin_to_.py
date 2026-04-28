"""add_description_website_linkedin_to_entreprise

Revision ID: 91e84d995c5f
Revises: 7e862c22b07f
Create Date: 2026-04-27 00:23:45.417706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91e84d995c5f'
down_revision: Union[str, None] = '7e862c22b07f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('entreprise', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('entreprise', sa.Column('website_url', sa.String(500), nullable=True))
    op.add_column('entreprise', sa.Column('linkedin_url', sa.String(500), nullable=True))

def downgrade():
    op.drop_column('entreprise', 'linkedin_url')
    op.drop_column('entreprise', 'website_url')
    op.drop_column('entreprise', 'description')