"""Add backup and backup_restore tables

Revision ID: add_backup_tables
Revises: add_lead_source_field
Create Date: 2025-12-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_backup_tables'
down_revision = 'add_lead_source_field'
branch_labels = None
depends_on = None


def upgrade():
    """Create backups and backup_restores tables"""

    # Create backups table
    op.create_table(
        'backups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('backup_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('storage_key', sa.String(1024), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.Column('database_name', sa.String(100), nullable=True),
        sa.Column('database_size_bytes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('job_id', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for backups table
    op.create_index('ix_backups_filename', 'backups', ['filename'])
    op.create_index('ix_backups_status', 'backups', ['status'])
    op.create_index('ix_backups_created_at', 'backups', ['created_at'])
    op.create_index('ix_backups_job_id', 'backups', ['job_id'])

    # Create backup_restores table
    op.create_table(
        'backup_restores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('backup_id', sa.Integer(), nullable=False),
        sa.Column('restored_by', sa.Integer(), nullable=False),
        sa.Column('pre_restore_backup_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['backup_id'], ['backups.id'], ),
        sa.ForeignKeyConstraint(['pre_restore_backup_id'], ['backups.id'], ),
        sa.ForeignKeyConstraint(['restored_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for backup_restores table
    op.create_index('ix_backup_restores_backup_id', 'backup_restores', ['backup_id'])


def downgrade():
    """Drop backup tables"""

    # Drop backup_restores table and indexes
    op.drop_index('ix_backup_restores_backup_id', table_name='backup_restores')
    op.drop_table('backup_restores')

    # Drop backups table and indexes
    op.drop_index('ix_backups_job_id', table_name='backups')
    op.drop_index('ix_backups_created_at', table_name='backups')
    op.drop_index('ix_backups_status', table_name='backups')
    op.drop_index('ix_backups_filename', table_name='backups')
    op.drop_table('backups')
