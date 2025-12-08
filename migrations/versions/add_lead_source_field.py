"""Add lead_source field to leads table

Revision ID: add_lead_source_field
Revises: add_performance_indexes
Create Date: 2025-11-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_lead_source_field'
down_revision = 'add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """Add lead_source column to leads table"""
    op.add_column('leads', sa.Column('lead_source', sa.String(50), nullable=True))
    op.create_index('ix_leads_lead_source', 'leads', ['lead_source'])


def downgrade():
    """Remove lead_source column from leads table"""
    op.drop_index('ix_leads_lead_source', table_name='leads')
    op.drop_column('leads', 'lead_source')
