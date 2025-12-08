"""Add critical indexes for performance

Revision ID: add_performance_indexes
Revises: 
Create Date: 2025-11-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = None  # Update this with your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes for common query patterns"""
    
    # Clients indexes
    op.create_index('ix_clients_tenant_id', 'clients', ['tenant_id'])
    op.create_index('ix_clients_deleted_at', 'clients', ['deleted_at'])
    op.create_index('ix_clients_assigned_to', 'clients', ['assigned_to'])
    op.create_index('ix_clients_created_by', 'clients', ['created_by'])
    op.create_index('ix_clients_created_at', 'clients', ['created_at'])
    
    # Composite indexes for clients
    op.create_index('ix_clients_tenant_deleted', 'clients', ['tenant_id', 'deleted_at'])
    op.create_index('ix_clients_tenant_assigned', 'clients', ['tenant_id', 'assigned_to'])
    
    # Leads indexes
    op.create_index('ix_leads_tenant_id', 'leads', ['tenant_id'])
    op.create_index('ix_leads_deleted_at', 'leads', ['deleted_at'])
    op.create_index('ix_leads_assigned_to', 'leads', ['assigned_to'])
    op.create_index('ix_leads_created_by', 'leads', ['created_by'])
    op.create_index('ix_leads_created_at', 'leads', ['created_at'])
    op.create_index('ix_leads_lead_status', 'leads', ['lead_status'])
    
    # Composite indexes for leads
    op.create_index('ix_leads_tenant_deleted', 'leads', ['tenant_id', 'deleted_at'])
    op.create_index('ix_leads_tenant_assigned', 'leads', ['tenant_id', 'assigned_to'])
    
    # Projects indexes
    op.create_index('ix_projects_tenant_id', 'projects', ['tenant_id'])
    op.create_index('ix_projects_deleted_at', 'projects', ['deleted_at'])
    op.create_index('ix_projects_client_id', 'projects', ['client_id'])
    op.create_index('ix_projects_lead_id', 'projects', ['lead_id'])
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])
    op.create_index('ix_projects_project_status', 'projects', ['project_status'])
    
    # Composite indexes for projects
    op.create_index('ix_projects_tenant_deleted', 'projects', ['tenant_id', 'deleted_at'])
    op.create_index('ix_projects_tenant_client', 'projects', ['tenant_id', 'client_id'])
    
    # Interactions indexes
    op.create_index('ix_interactions_tenant_id', 'interactions', ['tenant_id'])
    op.create_index('ix_interactions_client_id', 'interactions', ['client_id'])
    op.create_index('ix_interactions_lead_id', 'interactions', ['lead_id'])
    op.create_index('ix_interactions_project_id', 'interactions', ['project_id'])
    op.create_index('ix_interactions_contact_date', 'interactions', ['contact_date'])
    op.create_index('ix_interactions_completed', 'interactions', ['completed'])
    
    # Composite indexes for interactions
    op.create_index('ix_interactions_tenant_client', 'interactions', ['tenant_id', 'client_id'])
    op.create_index('ix_interactions_tenant_date', 'interactions', ['tenant_id', 'contact_date'])
    
    # Contacts indexes
    op.create_index('ix_contacts_tenant_id', 'contacts', ['tenant_id'])
    op.create_index('ix_contacts_client_id', 'contacts', ['client_id'])
    op.create_index('ix_contacts_lead_id', 'contacts', ['lead_id'])
    
    # Accounts indexes (if keeping accounts feature)
    op.create_index('ix_accounts_tenant_id', 'accounts', ['tenant_id'])
    op.create_index('ix_accounts_client_id', 'accounts', ['client_id'])
    
    # Activity log indexes
    op.create_index('ix_activity_log_tenant_id', 'activity_log', ['tenant_id'])
    op.create_index('ix_activity_log_user_id', 'activity_log', ['user_id'])
    op.create_index('ix_activity_log_timestamp', 'activity_log', ['timestamp'])
    op.create_index('ix_activity_log_entity', 'activity_log', ['entity_type', 'entity_id'])
    
    # Files indexes
    op.create_index('ix_files_tenant_id', 'files', ['tenant_id'])
    op.create_index('ix_files_uploaded_at', 'files', ['uploaded_at'])


def downgrade():
    """Remove performance indexes"""
    
    # Clients
    op.drop_index('ix_clients_tenant_id', table_name='clients')
    op.drop_index('ix_clients_deleted_at', table_name='clients')
    op.drop_index('ix_clients_assigned_to', table_name='clients')
    op.drop_index('ix_clients_created_by', table_name='clients')
    op.drop_index('ix_clients_created_at', table_name='clients')
    op.drop_index('ix_clients_tenant_deleted', table_name='clients')
    op.drop_index('ix_clients_tenant_assigned', table_name='clients')
    
    # Leads
    op.drop_index('ix_leads_tenant_id', table_name='leads')
    op.drop_index('ix_leads_deleted_at', table_name='leads')
    op.drop_index('ix_leads_assigned_to', table_name='leads')
    op.drop_index('ix_leads_created_by', table_name='leads')
    op.drop_index('ix_leads_created_at', table_name='leads')
    op.drop_index('ix_leads_lead_status', table_name='leads')
    op.drop_index('ix_leads_tenant_deleted', table_name='leads')
    op.drop_index('ix_leads_tenant_assigned', table_name='leads')
    
    # Projects
    op.drop_index('ix_projects_tenant_id', table_name='projects')
    op.drop_index('ix_projects_deleted_at', table_name='projects')
    op.drop_index('ix_projects_client_id', table_name='projects')
    op.drop_index('ix_projects_lead_id', table_name='projects')
    op.drop_index('ix_projects_created_at', table_name='projects')
    op.drop_index('ix_projects_project_status', table_name='projects')
    op.drop_index('ix_projects_tenant_deleted', table_name='projects')
    op.drop_index('ix_projects_tenant_client', table_name='projects')
    
    # Interactions
    op.drop_index('ix_interactions_tenant_id', table_name='interactions')
    op.drop_index('ix_interactions_client_id', table_name='interactions')
    op.drop_index('ix_interactions_lead_id', table_name='interactions')
    op.drop_index('ix_interactions_project_id', table_name='interactions')
    op.drop_index('ix_interactions_contact_date', table_name='interactions')
    op.drop_index('ix_interactions_completed', table_name='interactions')
    op.drop_index('ix_interactions_tenant_client', table_name='interactions')
    op.drop_index('ix_interactions_tenant_date', table_name='interactions')
    
    # Contacts
    op.drop_index('ix_contacts_tenant_id', table_name='contacts')
    op.drop_index('ix_contacts_client_id', table_name='contacts')
    op.drop_index('ix_contacts_lead_id', table_name='contacts')
    
    # Accounts
    op.drop_index('ix_accounts_tenant_id', table_name='accounts')
    op.drop_index('ix_accounts_client_id', table_name='accounts')
    
    # Activity log
    op.drop_index('ix_activity_log_tenant_id', table_name='activity_log')
    op.drop_index('ix_activity_log_user_id', table_name='activity_log')
    op.drop_index('ix_activity_log_timestamp', table_name='activity_log')
    op.drop_index('ix_activity_log_entity', table_name='activity_log')
    
    # Files
    op.drop_index('ix_files_tenant_id', table_name='files')
    op.drop_index('ix_files_uploaded_at', table_name='files')
