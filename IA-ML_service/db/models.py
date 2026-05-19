from numpy import positive
from alembic.util.sqla_compat import AUTOINCREMENT_DEFAULT
from sqlalchemy import (
    Column, String, Text, Float, Integer,
    DateTime, Date, func, ForeignKey,Boolean
)
from sqlalchemy.dialects.postgresql import JSONB
from db.database import Base
from sqlalchemy import LargeBinary
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base
class Potential_linkedin(Base):
    __tablename__ = "potential_linkedin"
    identifiant = Column(Integer, primary_key=True, autoincrement=True)
    posts = Column(JSONB, nullable=True)
    potential_score = Column(Integer, nullable=True)
    positive_signals = Column(JSONB, nullable=True)
    negative_signals = Column(JSONB, nullable=True)
    needs_it = Column(JSONB, nullable=True)
    recommandation = Column(String, nullable=True)
    emailsgenerated = Column(JSONB, nullable=True)
    identifiantEntreprise = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)



# metadata = MetaData(schema="public")
# Base = declarative_base(metadata=metadata)


class LeadsActivity(Base):
    __tablename__ = "leads_activity"
    __table_args__ = (
        UniqueConstraint("session_id", name="uq_leads_activity_session_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    full_visitor_id = Column(String(64), nullable=False, index=True)
    visit_id = Column(BigInteger, nullable=True)
    session_id = Column(String(160), nullable=False)
    visit_number = Column(Integer, nullable=True)
    visit_start_time = Column(DateTime(timezone=True), nullable=True)
    visit_date = Column(Date, nullable=True, index=True)
    visit_hour = Column(Integer, nullable=True)
    device_category = Column(String(80), nullable=True)
    browser = Column(String(160), nullable=True)
    operating_system = Column(String(160), nullable=True)
    country = Column(String(160), nullable=True)
    city = Column(String(160), nullable=True)
    traffic_source = Column(String(255), nullable=True)
    totals_pageviews = Column(Integer, nullable=False, default=0)
    totals_hits = Column(Integer, nullable=False, default=0)
    totals_bounces = Column(Integer, nullable=False, default=0)
    total_time_on_site = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class LeadSessionRaw(Base):
    __tablename__ = "lead_sessions_raw"
    __table_args__ = (
        UniqueConstraint("session_id", name="uq_lead_sessions_raw_session_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    full_visitor_id = Column(String(64), nullable=False, index=True)
    visit_id = Column(BigInteger, nullable=True)
    session_id = Column(String(160), nullable=False)
    visit_number = Column(Integer, nullable=True)
    visit_start_time = Column(DateTime(timezone=True), nullable=True)
    visit_date = Column(Date, nullable=True, index=True)
    visit_hour = Column(Integer, nullable=True)
    device_category = Column(String(80), nullable=True)
    browser = Column(String(160), nullable=True)
    operating_system = Column(String(160), nullable=True)
    country = Column(String(160), nullable=True)
    city = Column(String(160), nullable=True)
    traffic_source = Column(String(255), nullable=True)
    totals_pageviews = Column(Integer, nullable=False, default=0)
    totals_hits = Column(Integer, nullable=False, default=0)
    totals_bounces = Column(Integer, nullable=False, default=0)
    total_time_on_site = Column(Float, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LeadBehaviorFeature(Base):
    __tablename__ = "lead_behavior_features"
    __table_args__ = (
        UniqueConstraint("full_visitor_id", name="uq_lead_behavior_features_visitor"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    full_visitor_id = Column(String(64), nullable=False, index=True)
    nombre_sessions = Column(Integer, nullable=False, default=0)
    total_pageviews = Column(Float, nullable=False, default=0)
    avg_pageviews_per_session = Column(Float, nullable=False, default=0)
    total_hits = Column(Float, nullable=False, default=0)
    avg_hits_per_session = Column(Float, nullable=False, default=0)
    total_bounces = Column(Float, nullable=False, default=0)
    bounce_rate = Column(Float, nullable=False, default=0)
    total_time_on_site = Column(Float, nullable=False, default=0)
    avg_time_on_site = Column(Float, nullable=False, default=0)
    first_visit_date = Column(Date, nullable=True)
    last_visit_date = Column(Date, nullable=True, index=True)
    days_since_last_visit = Column(Integer, nullable=False, default=0)
    recency_score = Column(Float, nullable=False, default=0)
    suspicious_activity = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class LeadScore(Base):
    __tablename__ = "lead_scores"
    __table_args__ = (
        UniqueConstraint("full_visitor_id", name="uq_lead_scores_visitor"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    full_visitor_id = Column(String(64), nullable=False, index=True)
    lead_score = Column(Float, nullable=False, default=0)
    lead_score_100 = Column(Float, nullable=False, default=0)
    segment = Column(String(12), nullable=False, default="COLD")
    rank_position = Column(Integer, nullable=False, default=0)
    nombre_sessions_raw = Column(Float, nullable=False, default=0)
    avg_hits_per_session_raw = Column(Float, nullable=False, default=0)
    avg_pageviews_per_session_raw = Column(Float, nullable=False, default=0)
    bounce_rate_raw = Column(Float, nullable=False, default=0)
    recency_score_raw = Column(Float, nullable=False, default=0)
    nombre_sessions_scaled = Column(Float, nullable=False, default=0)
    avg_hits_per_session_scaled = Column(Float, nullable=False, default=0)
    avg_pageviews_per_session_scaled = Column(Float, nullable=False, default=0)
    bounce_score = Column(Float, nullable=False, default=0)
    suspicious_activity = Column(Integer, nullable=False, default=0)
    scored_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LeadNotification(Base):
    __tablename__ = "lead_notifications"
    __table_args__ = (
        UniqueConstraint(
            "full_visitor_id",
            "notification_type",
            "last_visit_date",
            name="uq_lead_notifications_daily_type",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    full_visitor_id = Column(String(64), nullable=False, index=True)
    notification_type = Column(String(60), nullable=False)
    message = Column(Text, nullable=False)
    old_score = Column(Float, nullable=True)
    new_score = Column(Float, nullable=True)
    old_segment = Column(String(12), nullable=True)
    new_segment = Column(String(12), nullable=True)
    last_visit_date = Column(Date, nullable=True, index=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    

    
    