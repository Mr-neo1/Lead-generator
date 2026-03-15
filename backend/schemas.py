"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
import re
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class LeadType(str, Enum):
    NO_WEBSITE = "NO_WEBSITE"
    WEBSITE_REDESIGN = "WEBSITE_REDESIGN"
    NORMAL = "NORMAL"
    UNKNOWN = "UNKNOWN"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    CONVERTED = "converted"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# Request schemas
class JobCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100, description="Search keyword")
    location: str = Field(..., min_length=1, max_length=200, description="Location name")
    radius: int = Field(..., ge=1, le=100, description="Search radius in km")
    grid_size: str = Field(default="10x10", pattern=r"^\d+x\d+$", description="Grid density (e.g., 10x10)")


class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")
    notes: Optional[str] = Field(None, max_length=2000)
    is_blacklisted: Optional[bool] = None
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v and len(v.split(',')) > 20:
            raise ValueError('Maximum 20 tags allowed')
        return v
    
    @field_validator('notes')
    @classmethod
    def validate_notes(cls, v):
        if v and '<script>' in v.lower():
            raise ValueError('HTML/Script tags not allowed in notes')
        return v


class BulkLeadUpdate(BaseModel):
    lead_ids: List[int] = Field(..., min_length=1, max_length=100)
    status: Optional[LeadStatus] = None
    tags: Optional[str] = None
    is_blacklisted: Optional[bool] = None


class BulkDeleteRequest(BaseModel):
    lead_ids: List[int] = Field(..., min_length=1, max_length=100)


class BlacklistCreate(BaseModel):
    value: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., pattern=r"^(phone|place_id)$")
    reason: Optional[str] = Field(None, max_length=500)


# Response schemas
class JobResponse(BaseModel):
    job_id: str
    status: str
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class JobDetailResponse(BaseModel):
    job_id: str
    keyword: str
    location: str
    radius: int
    grid_size: str
    status: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    leads_found: int
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    progress_percent: float = 0.0
    
    model_config = ConfigDict(from_attributes=True)


class LeadResponse(BaseModel):
    id: int
    place_id: str
    name: str
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    category: Optional[str] = None
    address: Optional[str] = None
    maps_url: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None
    status: str
    is_blacklisted: bool
    type: str = "UNKNOWN"
    score: int = 0
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class PaginatedLeadsResponse(BaseModel):
    items: List[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedJobsResponse(BaseModel):
    items: List[JobDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StatsResponse(BaseModel):
    totalBusinesses: int
    qualifiedLeads: int
    noWebsiteLeads: int
    activeJobs: int
    completedJobs: int


class AdvancedStatsResponse(BaseModel):
    leadTypeDistribution: dict
    scoreDistribution: List[dict]
    topCategories: List[dict]
    topLeads: List[dict]
    recentJobs: List[dict]
    averageRating: float
    statusDistribution: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    version: str = "1.0.0"


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

