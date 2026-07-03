"""email_template_partner_scope

Revision ID: e0a1f2b3c4e3
Revises: e0a1f2b3c4e2
Create Date: 2026-07-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'e0a1f2b3c4e3'
down_revision: Union[str, None] = 'e0a1f2b3c4e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('email_templates', sa.Column('partner_id', UUID(as_uuid=True),
                                               sa.ForeignKey('partners.id'), nullable=True))
    op.drop_index('ix_email_templates_slug', table_name='email_templates')
    op.create_index('ix_email_templates_slug', 'email_templates', ['slug'], unique=False)
    # System default (partner_id IS NULL): one row per slug.
    op.create_index(
        'uq_email_templates_slug_default', 'email_templates', ['slug'],
        unique=True, postgresql_where=sa.text('partner_id IS NULL'),
    )
    # Partner override: one row per (slug, partner_id).
    op.create_index(
        'uq_email_templates_slug_partner', 'email_templates', ['slug', 'partner_id'],
        unique=True, postgresql_where=sa.text('partner_id IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('uq_email_templates_slug_partner', table_name='email_templates')
    op.drop_index('uq_email_templates_slug_default', table_name='email_templates')
    op.drop_index('ix_email_templates_slug', table_name='email_templates')
    op.create_index('ix_email_templates_slug', 'email_templates', ['slug'], unique=True)
    op.drop_column('email_templates', 'partner_id')
