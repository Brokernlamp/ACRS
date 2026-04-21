from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date,
    Numeric, Text, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    agency_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String(50), default="free")
    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    api_connections = relationship("APIConnection", back_populates="user", cascade="all, delete-orphan")


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_client_name"),)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    industry = Column(String(100))
    target_cpl = Column(Numeric(10, 2))
    monthly_budget = Column(Numeric(10, 2))
    revenue_per_lead = Column(Numeric(10, 2))  # enables P&L calculation
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    user = relationship("User", back_populates="clients")
    campaigns = relationship("Campaign", back_populates="client", cascade="all, delete-orphan")
    campaign_groups = relationship("CampaignGroup", back_populates="client", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="client", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="client", cascade="all, delete-orphan")


class CampaignGroup(Base):
    """
    A logical container that groups campaigns from different platforms
    that serve the same objective for the same client.
    e.g. 'Retargeting' group = Google Display + Meta Retargeting
    """
    __tablename__ = "campaign_groups"
    __table_args__ = (UniqueConstraint("client_id", "name", name="uq_client_group_name"),)
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)          # e.g. "Retargeting"
    objective = Column(String(50), default="conversion") # awareness | consideration | conversion
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    client = relationship("Client", back_populates="campaign_groups")
    campaigns = relationship("Campaign", back_populates="group")


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(Integer, ForeignKey("campaign_groups.id", ondelete="SET NULL"), nullable=True)
    campaign_name = Column(String(255), nullable=False)
    platform = Column(String(50), default="manual")  # google_ads | meta_ads | linkedin | manual
    platform_campaign_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    client = relationship("Client", back_populates="campaigns")
    group = relationship("CampaignGroup", back_populates="campaigns")
    data = relationship("CampaignData", back_populates="campaign", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="campaign")


class CampaignData(Base):
    __tablename__ = "campaign_data"
    __table_args__ = (UniqueConstraint("campaign_id", "date", name="uq_campaign_date"),)
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    spend = Column(Numeric(10, 2), default=0)
    leads = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Numeric(10, 2), default=0)
    ctr = Column(Numeric(5, 2))
    cpl = Column(Numeric(10, 2))
    conversion_rate = Column(Numeric(5, 2))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="data")


class APIConnection(Base):
    __tablename__ = "api_connections"
    __table_args__ = (UniqueConstraint("user_id", "platform", name="uq_user_platform"),)
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)  # 'google_ads', 'meta_ads'
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    account_id = Column(String(255))
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_connections")


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="SET NULL"))
    alert_type = Column(String(50))  # 'cpl_spike', 'ctr_drop', 'budget_pacing', 'zero_conversions'
    severity = Column(String(20))  # 'low', 'medium', 'high', 'critical'
    message = Column(Text)
    metric_value = Column(Numeric(10, 2))
    threshold_value = Column(Numeric(10, 2))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    client = relationship("Client", back_populates="alerts")
    campaign = relationship("Campaign", back_populates="alerts")


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String(50))  # 'standard', 'growth_strategy'
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    pdf_path = Column(String(500))
    generated_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    
    # Relationships
    client = relationship("Client", back_populates="reports")
