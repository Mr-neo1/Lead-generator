from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class ScrapingJob(Base):
    """Scraping job configuration and progress tracking."""
    __tablename__ = "scraping_jobs"
    
    job_id = Column(String, primary_key=True, index=True)
    keyword = Column(String, index=True)
    location = Column(String, index=True)
    radius = Column(Integer)
    grid_size = Column(String)
    status = Column(String, default="pending", index=True)  # pending, running, paused, completed, failed
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    leads_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to businesses found by this job
    businesses = relationship("Business", back_populates="job")


class Business(Base):
    """Scraped business/lead information."""
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, unique=True, index=True)
    source_job_id = Column(String, ForeignKey("scraping_jobs.job_id"), nullable=True, index=True)
    name = Column(String, index=True)
    phone = Column(String, nullable=True, index=True)
    website = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    reviews = Column(Integer, nullable=True)
    category = Column(String, nullable=True, index=True)
    address = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    maps_url = Column(String)
    
    # Lead management
    tags = Column(String, nullable=True)  # Comma-separated tags
    notes = Column(Text, nullable=True)
    status = Column(String, default="new", index=True)  # new, contacted, qualified, rejected, converted
    is_blacklisted = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    job = relationship("ScrapingJob", back_populates="businesses")
    analysis = relationship("LeadAnalysis", back_populates="business", uselist=False)
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_business_category_status', 'category', 'status'),
        Index('ix_business_phone_blacklist', 'phone', 'is_blacklisted'),
    )


class LeadAnalysis(Base):
    """Website analysis and lead scoring data."""
    __tablename__ = "lead_analysis"
    
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), primary_key=True)
    lead_type = Column(String, index=True)  # NO_WEBSITE, WEBSITE_REDESIGN, NORMAL
    lead_score = Column(Integer, default=0, index=True)
    ssl_enabled = Column(Boolean, default=False)
    mobile_friendly = Column(Boolean, default=False)
    load_time = Column(Float, nullable=True)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    business = relationship("Business", back_populates="analysis")
    
    # Index for filtering by type and score
    __table_args__ = (
        Index('ix_lead_type_score', 'lead_type', 'lead_score'),
    )


class Blacklist(Base):
    """Phone numbers or place IDs to skip during scraping."""
    __tablename__ = "blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    value = Column(String, unique=True, index=True)  # Phone number or place_id
    type = Column(String, index=True)  # phone, place_id
    reason = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JobLog(Base):
    """Detailed logs for debugging scraping issues."""
    __tablename__ = "job_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("scraping_jobs.job_id", ondelete="CASCADE"), index=True)
    level = Column(String)  # INFO, WARNING, ERROR
    message = Column(Text)
    details = Column(Text, nullable=True)  # JSON string for extra data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('ix_job_log_job_level', 'job_id', 'level'),
    )

