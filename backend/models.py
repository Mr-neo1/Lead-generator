from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"
    job_id = Column(String, primary_key=True, index=True)
    keyword = Column(String)
    location = Column(String)
    radius = Column(Integer)
    grid_size = Column(String)
    status = Column(String, default="pending")
    total_tasks = Column(Integer, default=0)  # Total grid points to scrape
    completed_tasks = Column(Integer, default=0)  # Completed grid points
    leads_found = Column(Integer, default=0)  # Total businesses found
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Business(Base):
    __tablename__ = "businesses"
    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(String, unique=True, index=True) # Used for deduplication
    name = Column(String)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    reviews = Column(Integer, nullable=True)
    category = Column(String, nullable=True)
    address = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    maps_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LeadAnalysis(Base):
    __tablename__ = "lead_analysis"
    business_id = Column(Integer, ForeignKey("businesses.id"), primary_key=True)
    lead_type = Column(String) # NO_WEBSITE, WEBSITE_REDESIGN, NORMAL
    lead_score = Column(Integer, default=0)
    ssl_enabled = Column(Boolean, default=False)
    mobile_friendly = Column(Boolean, default=False)
    load_time = Column(Float, nullable=True)

class DemoSite(Base):
    __tablename__ = "demo_sites"
    business_id = Column(Integer, ForeignKey("businesses.id"), primary_key=True)
    demo_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
