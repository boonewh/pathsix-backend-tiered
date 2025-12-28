from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Table, Boolean, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy import Enum, Index, UniqueConstraint, JSON
import enum

# Association table for many-to-many User ↔ Role
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id')),
)

# === Tiered Pricing Enums ===

class TenantStatus(enum.Enum):
    active = "active"
    read_only = "read_only"  # Over quota
    suspended = "suspended"  # Payment failed
    cancelled = "cancelled"

class SubscriptionStatus(enum.Enum):
    active = "active"
    past_due = "past_due"
    canceled = "canceled"
    incomplete = "incomplete"
    trialing = "trialing"

class EmailVerificationStatus(enum.Enum):
    pending = "pending"
    verified = "verified"
    expired = "expired"

class FollowUpStatus(enum.Enum):
    pending = "pending"
    contacted = "contacted"
    completed = "completed"
    rescheduled = "rescheduled"


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)  # Will add FK constraint in migration
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True)

    # Email verification for tiered pricing
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    roles = relationship("Role", secondary=user_roles, back_populates="users")

    def __repr__(self):
        return f"<User {self.email}>"


class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", secondary=user_roles, back_populates="roles")

    def __repr__(self):
        return f"<Role {self.name}>"


# === Tiered Pricing Models ===

class Tenant(Base):
    """
    Tenant model for multi-tenancy with tiered pricing.
    Converts tenant_id from just an integer to a full model with billing info.
    """
    __tablename__ = 'tenants'

    # Primary key
    id = Column(Integer, primary_key=True)

    # Stripe integration
    stripe_customer_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)

    # Plan details
    plan_tier = Column(String(20), default='free', nullable=False, index=True)
    # Valid values: 'free', 'starter', 'business', 'enterprise'

    # Status
    status = Column(Enum(TenantStatus), default=TenantStatus.active, nullable=False, index=True)

    # Billing
    billing_email = Column(String(120), nullable=True, index=True)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)

    # Metadata
    company_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Trial tracking (optional for future)
    trial_ends_at = Column(DateTime, nullable=True)

    # Relationships (using primaryjoin since tenant_id is not a proper FK yet)
    users = relationship("User",
                        primaryjoin="Tenant.id==User.tenant_id",
                        foreign_keys="User.tenant_id",
                        backref="tenant",
                        viewonly=True)

    __table_args__ = (
        Index('idx_tenant_stripe_lookup', 'stripe_customer_id'),
        Index('idx_tenant_plan_status', 'plan_tier', 'status'),
    )

    def __repr__(self):
        return f"<Tenant id={self.id} plan={self.plan_tier} status={self.status.value}>"


class PlanLimit(Base):
    """
    Plan limits configuration table.
    Stores the quota limits for each tier (free, starter, business, enterprise).
    """
    __tablename__ = 'plan_limits'

    id = Column(Integer, primary_key=True)
    plan_tier = Column(String(20), unique=True, nullable=False, index=True)

    # User limits
    max_users = Column(Integer, nullable=False)  # -1 for unlimited

    # Storage limits (bytes)
    max_storage_bytes = Column(BigInteger, nullable=False)  # -1 for unlimited

    # Database record limits
    max_db_records = Column(Integer, nullable=False)  # -1 for unlimited

    # API rate limits
    max_api_calls_per_day = Column(Integer, nullable=False)

    # Email limits
    max_emails_per_month = Column(Integer, nullable=False)

    # Feature flags (JSON for extensibility)
    features = Column(JSON, default={}, nullable=False)
    # Example: {"advanced_reporting": true, "api_access": true}

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_plan_tier', 'plan_tier'),
    )

    def __repr__(self):
        return f"<PlanLimit {self.plan_tier}>"


class TenantUsage(Base):
    """
    Tracks resource usage per tenant for quota enforcement.
    Updated in real-time via background jobs to avoid slowing API responses.
    """
    __tablename__ = 'tenant_usage'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, index=True)

    # Current usage counters
    storage_bytes = Column(BigInteger, default=0, nullable=False)
    db_record_count = Column(Integer, default=0, nullable=False)
    api_calls_today = Column(Integer, default=0, nullable=False)
    emails_this_month = Column(Integer, default=0, nullable=False)

    # Reset tracking
    api_calls_reset_at = Column(DateTime, nullable=False)  # Daily reset
    emails_reset_at = Column(DateTime, nullable=False)  # Monthly reset

    # Cache for limits (denormalized for performance)
    cached_max_storage = Column(BigInteger, nullable=True)
    cached_max_records = Column(Integer, nullable=True)
    cached_max_api_calls = Column(Integer, nullable=True)
    cached_max_emails = Column(Integer, nullable=True)
    cached_limits_updated_at = Column(DateTime, nullable=True)

    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Relationships
    tenant = relationship("Tenant", backref="usage")

    __table_args__ = (
        Index('idx_tenant_usage_lookup', 'tenant_id'),
        UniqueConstraint('tenant_id', name='uq_tenant_usage_tenant'),
    )

    def __repr__(self):
        return f"<TenantUsage tenant_id={self.tenant_id} storage={self.storage_bytes} records={self.db_record_count}>"


class Subscription(Base):
    """
    Stripe subscription tracking for paid tiers.
    Synced via Stripe webhooks.
    """
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, index=True)

    # Stripe data
    stripe_subscription_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String(255), nullable=False, index=True)
    stripe_price_id = Column(String(255), nullable=False)  # Stripe Price ID

    # Plan details
    plan_tier = Column(String(20), nullable=False)
    amount_cents = Column(Integer, nullable=False)  # Price in cents
    currency = Column(String(3), default='usd', nullable=False)

    # Status
    status = Column(Enum(SubscriptionStatus), nullable=False, index=True)

    # Billing cycle
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)

    # Trial
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", backref="subscriptions")

    __table_args__ = (
        Index('idx_subscription_stripe', 'stripe_subscription_id'),
        Index('idx_subscription_status', 'tenant_id', 'status'),
    )

    def __repr__(self):
        return f"<Subscription tenant_id={self.tenant_id} status={self.status.value}>"


class EmailVerification(Base):
    """
    Email verification tokens for signup flow.
    Required to prevent spam/abuse on free tier.
    """
    __tablename__ = 'email_verifications'

    id = Column(Integer, primary_key=True)
    email = Column(String(120), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(Enum(EmailVerificationStatus), default=EmailVerificationStatus.pending, nullable=False)

    # Associated data for signup
    tenant_id = Column(Integer, nullable=True)  # Set after verification
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Expiration
    expires_at = Column(DateTime, nullable=False, index=True)
    verified_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_email_verification_token', 'token'),
        Index('idx_email_verification_status', 'email', 'status'),
    )

    def __repr__(self):
        return f"<EmailVerification email={self.email} status={self.status.value}>"


class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    deleted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=True)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    contact_title = Column(String(100))
    email = Column(String(120), index=True)
    phone = Column(String(20))
    phone_label = Column(String(20), default="work")
    secondary_phone = Column(String(20), nullable=True)
    secondary_phone_label = Column(String(20), nullable=True)
    address = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    zip = Column(String(20))
    status = Column(String(50), default='new')
    type = Column(String(50), nullable=True, default="None")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    created_by_user = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Client {self.name}>"


class Account(Base):
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    tenant_id = Column(Integer, nullable=False)
    account_number = Column(String(100), nullable=False, unique=True)
    account_name = Column(String(255), nullable=True)
    status = Column(String(50), default="active")
    opened_on = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)

    client = relationship("Client", backref="accounts")

    def __repr__(self):
        return f"<Account {self.account_number}>"


class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=True)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    contact_title = Column(String(100))
    email = Column(String(120), index=True)
    phone = Column(String(20))
    phone_label = Column(String(20), default="work")
    secondary_phone = Column(String(20), nullable=True)
    secondary_phone_label = Column(String(20), nullable=True)
    address = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    zip = Column(String(20))
    type = Column(String(50), nullable=True, default="None")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    lead_status = Column(String(20), default="open")  # Valid: "open", "converted", "closed", "lost"
    converted_on = Column(DateTime, nullable=True)
    lead_source = Column(String(50), nullable=True, index=True)  # Website, Referral, Cold Call, Email Campaign, etc.

    assigned_user = relationship("User", foreign_keys=[assigned_to])
    created_by_user = relationship("User", foreign_keys=[created_by])


    def __repr__(self):
        return f"<Lead {self.name}>"
    

class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)

    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=True)

    first_name = Column(String(100))
    last_name = Column(String(100))
    title = Column(String(100))
    email = Column(String(120), index=True)
    phone = Column(String(20))
    phone_label = Column(String(20), default="work")
    secondary_phone = Column(String(20), nullable=True)
    secondary_phone_label = Column(String(20), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", backref="contacts")
    lead = relationship("Lead", backref="contacts")

    def to_dict(self):
        return {
            "id": self.id,
            "name": f"{self.first_name} {self.last_name}".strip(),
            "title": self.title,
            "email": self.email,
            "phone": self.phone,
            "phone_label": self.phone_label,
        }

    def __repr__(self):
        return f"<Contact {self.first_name} {self.last_name}>"


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    tenant_id = Column(Integer, nullable=False)
    project_name = Column(String(255), nullable=False)
    project_description = Column(Text, nullable=True)
    type = Column(String(50), nullable=True, default="None")
    primary_contact_name = Column(String(100), nullable=True)
    primary_contact_title = Column(String(100), nullable=True)
    primary_contact_email = Column(String(120), nullable=True)
    primary_contact_phone = Column(String(20), nullable=True)
    primary_contact_phone_label = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    project_status = Column(String(20), nullable=False) # Valid values: "pending", "won", "lost"
    project_start = Column(DateTime, nullable=True)
    project_end = Column(DateTime, nullable=True)
    project_worth = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    last_updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # ✅ Relationships to access names in API
    client = relationship("Client", backref="projects")
    lead = relationship("Lead", backref="projects")

    def __repr__(self):
        return f"<Project {self.project_name}>"
    

class Interaction(Base):
    __tablename__ = 'interactions'

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)  # 🆕 NEW FIELD
    tenant_id = Column(Integer, nullable=False)
    contact_person = Column(String)
    email = Column(String)
    phone = Column(String)
    contact_date = Column(DateTime, default=datetime.utcnow)
    outcome = Column(String(255))
    notes = Column(Text)
    follow_up = Column(DateTime, nullable=True)
    followup_status = Column(Enum(FollowUpStatus), default=FollowUpStatus.pending, nullable=False)
    summary = Column(String(255))

    # Relationships
    lead = relationship("Lead", backref="interactions")
    client = relationship("Client", backref="interactions")
    project = relationship("Project", backref="interactions")  # 🆕 NEW RELATIONSHIP

    def __repr__(self):
        return f"<Interaction {self.id} on {self.contact_date}>"
    

class ActivityType(enum.Enum):
    viewed = "viewed"
    created = "created"
    edited = "edited"
    deleted = "deleted"

class ActivityLog(Base):
    __tablename__ = 'activity_logs'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(Enum(ActivityType), nullable=False)
    entity_type = Column(String(50), nullable=False)  # "client", "lead"
    entity_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    description = Column(Text)

    def __repr__(self):
        return f"<ActivityLog {self.action.value} {self.entity_type} {self.entity_id}>"


class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # null for room chats
    room = Column(String(100), nullable=True)  # null for direct messages
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    lead_id = Column(Integer, ForeignKey('leads.id'), nullable=True)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    client = relationship("Client", backref="chat_messages")
    lead = relationship("Lead", backref="chat_messages")

    def __repr__(self):
        target = self.room or self.recipient_id
        return f"<ChatMessage from {self.sender_id} to {target}>"


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class UserPreference(Base):
    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    preference_key = Column(String(100), nullable=False, index=True)
    preference_value = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="preferences")

    # Constraints
    __table_args__ = (
        Index('idx_user_preferences_lookup', 'user_id', 'category', 'preference_key'),
        UniqueConstraint('user_id', 'category', 'preference_key', name='uq_user_category_key'),
    )

    def __repr__(self):
        return f"<UserPreference user_id={self.user_id} {self.category}.{self.preference_key}>"
    

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Original name the user uploaded (safe to show in UI / as download name)
    filename = Column(String(255), nullable=False)

    # Internal stored filename (e.g., "<uuid>.ext"); helpful when using local disk
    stored_name = Column(String(255), nullable=False)

    # STORAGE-AGNOSTIC POINTER:
    # - Local disk: absolute or normalized relative path (e.g., "./storage/12/<uuid>.pdf")
    # - Backblaze B2: object key within the bucket (e.g., "tenant-12/<uuid>.pdf")
    path = Column(String(1024), nullable=False, index=True)

    size = Column(Integer, nullable=False)          # bytes
    mimetype = Column(String(100), nullable=False)  # e.g., "application/pdf"
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    uploader = relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.filename,
            "size": self.size,
            "uploadedBy": self.uploader.email if self.uploader else None,
            "date": (self.uploaded_at.isoformat() + "Z") if self.uploaded_at else None,
            "mimetype": self.mimetype,
        }

    def __repr__(self):
        return f"<File id={self.id} tenant={self.tenant_id} name={self.filename}>"


class Backup(Base):
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True)

    # Backup metadata
    filename = Column(String(255), nullable=False, index=True)
    backup_type = Column(String(20), default="manual", nullable=False)  # manual|scheduled|pre_restore
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending|in_progress|completed|failed

    # Storage location
    storage_key = Column(String(1024), nullable=True)  # B2 object key
    size_bytes = Column(Integer, nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA-256 checksum

    # Database snapshot metadata
    database_name = Column(String(100), nullable=True)
    database_size_bytes = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Job tracking
    job_id = Column(String(100), nullable=True, index=True)  # RQ job ID

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Audit trail
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "type": self.backup_type,
            "status": self.status,
            "size": self.size_bytes,
            "database_size": self.database_size_bytes,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "completed_at": self.completed_at.isoformat() + "Z" if self.completed_at else None,
            "created_by": self.creator.email if self.creator else "system",
            "error": self.error_message,
        }

    def __repr__(self):
        return f"<Backup {self.filename} status={self.status}>"


class BackupRestore(Base):
    __tablename__ = "backup_restores"

    id = Column(Integer, primary_key=True)
    backup_id = Column(Integer, ForeignKey("backups.id"), nullable=False, index=True)
    restored_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Pre-restore safety snapshot (automatic backup before restore)
    pre_restore_backup_id = Column(Integer, ForeignKey("backups.id"), nullable=True)

    status = Column(String(20), default="in_progress", nullable=False)  # in_progress|completed|failed
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    backup = relationship("Backup", foreign_keys=[backup_id])
    pre_restore_backup = relationship("Backup", foreign_keys=[pre_restore_backup_id])
    restorer = relationship("User", foreign_keys=[restored_by])

    def to_dict(self):
        return {
            "id": self.id,
            "backup_id": self.backup_id,
            "pre_restore_backup_id": self.pre_restore_backup_id,
            "restored_by": self.restorer.email if self.restorer else None,
            "status": self.status,
            "started_at": self.started_at.isoformat() + "Z" if self.started_at else None,
            "completed_at": self.completed_at.isoformat() + "Z" if self.completed_at else None,
            "error": self.error_message,
        }

    def __repr__(self):
        return f"<BackupRestore backup_id={self.backup_id} status={self.status}>"
