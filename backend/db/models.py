import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default='Recruiter')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)

    # Relationships
    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")


class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    billing_tier = Column(String(50), default='Free')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="organization", uselist=False, cascade="all, delete-orphan")
    candidates = relationship("Candidate", back_populates="organization", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    __tablename__ = 'organization_members'

    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(50), default='Recruiter')  # Owner, Admin, Recruiter, Hiring Manager, Viewer
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")


class OrganizationInvitation(Base):
    __tablename__ = 'organization_invitations'

    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    role = Column(String(50), default='Recruiter')
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="invitations")


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    plan_name = Column(String(50), default='Free')  # Free, Pro, Business, Enterprise
    status = Column(String(50), default='active')    # active, past_due, canceled
    current_period_end = Column(DateTime, nullable=True)
    
    # Usage metrics tracked for the current billing period
    cv_parses_used = Column(Integer, default=0)
    jobs_created_used = Column(Integer, default=0)
    team_seats_used = Column(Integer, default=1)
    
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="subscription")


class Candidate(Base):
    __tablename__ = 'candidates'

    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # PII Fields - stored encrypted at rest
    name = Column(String(512), nullable=False)   # Encrypted
    email = Column(String(512), nullable=True)   # Encrypted
    
    role = Column(String(255))
    github = Column(String(255))
    linkedin = Column(String(255))
    location = Column(String(255))
    score = Column(Integer, default=0)
    blind_score = Column(Integer, default=0)
    status = Column(String(50), default='Match')
    summary = Column(Text)
    resume_text = Column(Text)
    skills = Column(Text)          # JSON Array string
    experience = Column(Text)      # JSON Array string
    job_matches = Column(Text)     # JSON Array string
    radar_data = Column(Text)      # JSON Array string
    qa = Column(Text)              # JSON string
    insights = Column(Text)        # JSON string
    analyzed_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="candidates")


class Job(Base):
    __tablename__ = 'jobs'

    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), default='HireIQ Corp')
    department = Column(String(255))
    employment_type = Column(String(100))
    location = Column(String(255))
    description = Column(Text)
    required_skills = Column(Text)
    preferred_skills = Column(Text)
    experience_required = Column(Integer, default=0)
    max_experience = Column(Integer, default=99)
    salary_range = Column(String(100))
    status = Column(String(50), default='Open')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="jobs")


class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    organization_id = Column(String(36), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    organization = relationship("Organization", back_populates="audit_logs")


class StripeWebhookEvent(Base):
    __tablename__ = 'stripe_webhook_events'

    id = Column(String(255), primary_key=True)  # stripe event id
    event_type = Column(String(255), nullable=False)
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)
    payload = Column(Text, nullable=False)
    status = Column(String(50), default='processed')  # processed, failed, retried
    error_message = Column(Text, nullable=True)
