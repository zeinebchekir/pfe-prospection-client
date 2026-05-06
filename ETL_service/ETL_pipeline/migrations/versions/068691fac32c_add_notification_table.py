"""add notification table 

Revision ID: 068691fac32c
Revises: 4364828197a5
Create Date: 2026-05-06 12:00:07.977518

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '068691fac32c'
down_revision: Union[str, None] = '4364828197a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Création de la table notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dag_id', sa.Text(), nullable=False),
        sa.Column('task_id', sa.Text(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # Création de l'index sur l'id
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)

    # 2. Correction du changement de type (si pas encore fait)
    # On ajoute le "postgresql_using" pour éviter l'erreur de cast


def downgrade() -> None:
    # On annule les changements en sens inverse
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    
    # On repasse l'identifiant en string si besoin
