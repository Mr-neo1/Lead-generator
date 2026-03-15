"""
Lead Engine API - Main Application
FastAPI backend with pagination, rate limiting, caching, and improved error handling.
"""

from fastapi import FastAPI, Depends, Query, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
import uuid
import csv
import io
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List
from math import ceil

# Local imports
from database import engine, Base, get_db, init_db, check_db_connection
from models import ScrapingJob, Business, LeadAnalysis, Blacklist, JobLog
from schemas import (
    JobCreate, JobResponse, JobDetailResponse, LeadResponse, 
    PaginatedLeadsResponse, PaginatedJobsResponse, StatsResponse,
    AdvancedStatsResponse, HealthResponse, MessageResponse, ErrorResponse,
    LeadUpdate, BulkLeadUpdate, BulkDeleteRequest, BlacklistCreate
)
from grid_generator import generate_grid
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Audit logger
audit_logger = logging.getLogger("audit")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Optional Redis support
USE_REDIS = settings.use_redis
redis_conn = None
q_discovery = None

if USE_REDIS:
    try:
        from redis import Redis
        from rq import Queue
        redis_conn = Redis.from_url(settings.redis_url)
        q_discovery = Queue('discovery', connection=redis_conn)
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        USE_REDIS = False

# Simple in-memory cache for stats (resets on restart)
stats_cache = {"data": None, "expires": None}
STATS_CACHE_TTL = 60  # seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("Starting Lead Engine API...")
    
    # Validate critical configuration
    if not settings.api_key or settings.api_key == "":
        if settings.use_redis or not settings.debug:
            logger.error("CRITICAL: API_KEY not configured! Set API_KEY environment variable.")
            raise RuntimeError("API_KEY environment variable is required for production. Refusing to start.")
        else:
            logger.warning("API_KEY not set — running in LOCAL DEV mode (no auth enforcement).")
    
    if settings.api_key == "change-me-in-production":
        logger.error("CRITICAL: API_KEY still set to default value!")
        raise RuntimeError("API_KEY must be changed from default. Refusing to start.")
    
    init_db()
    logger.info("Lead Engine API started successfully")
    yield
    # Shutdown
    logger.info("Shutting down Lead Engine API...")


# Create FastAPI app
app = FastAPI(
    title="Lead Engine API",
    description="Automated Lead Generation System with Google Maps scraping",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Audit logging middleware
@app.middleware("http")
async def audit_logging_middleware(request: Request, call_next):
    """Log all write operations for compliance and debugging."""
    start_time = time.time()
    
    # Only log write operations
    if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
        client_ip = request.client.host if request.client else "unknown"
        audit_logger.info(
            f"{request.method} {request.url.path} - {client_ip}"
        )
    
    response = await call_next(request)
    
    # Log slow requests
    process_time = time.time() - start_time
    if process_time > 5.0:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s")
    
    return response


# API Key auth
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key - REQUIRED for all protected endpoints.
    Skipped when API_KEY is not configured (local dev mode)."""
    # In local dev mode (no API key configured), skip auth
    if not settings.api_key:
        return True
    if not api_key:
        raise HTTPException(
            status_code=401, 
            detail="API key required. Set X-API-Key header."
        )
    if api_key != settings.api_key:
        logger.warning("Authentication failed - invalid API key attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"}
    )


# Health check endpoints
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration."""
    db_status = "healthy" if check_db_connection() else "unhealthy"
    redis_status = "disabled"
    
    if USE_REDIS and redis_conn:
        try:
            redis_conn.ping()
            redis_status = "healthy"
        except:
            redis_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "redis": redis_status,
        "version": "1.0.0"
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check for Kubernetes."""
    if not check_db_connection():
        raise HTTPException(status_code=503, detail="Database not ready")
    return {"status": "ready"}


# Jobs endpoints
@app.post("/api/jobs", response_model=JobResponse, tags=["Jobs"])
@limiter.limit("3/minute")  # Tight limit: each job spawns N Playwright browser processes
async def create_job(
    request: Request,
    job: JobCreate, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Create a new scraping job."""
    job_id = f"JOB-{str(uuid.uuid4())[:8].upper()}"
    
    try:
        coordinates = generate_grid(job.location, job.radius, job.grid_size)
        total_tasks = len(coordinates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid location: {str(e)}")
    
    new_job = ScrapingJob(
        job_id=job_id,
        keyword=job.keyword,
        location=job.location,
        radius=job.radius,
        grid_size=job.grid_size,
        status="pending" if not USE_REDIS else "running",
        total_tasks=total_tasks,
        completed_tasks=0,
        failed_tasks=0,
        leads_found=0
    )
    db.add(new_job)
    db.commit()
    
    # Log job creation
    log_entry = JobLog(
        job_id=job_id,
        level="INFO",
        message=f"Job created with {total_tasks} grid points"
    )
    db.add(log_entry)
    db.commit()
    
    if USE_REDIS and q_discovery:
        for lat, lng in coordinates:
            q_discovery.enqueue('tasks.run_discovery', job_id, job.keyword, lat, lng)
    
    logger.info(f"Created job {job_id} for {job.keyword} in {job.location}")
    return {"job_id": job_id, "status": new_job.status, "message": f"Created with {total_tasks} tasks"}


@app.get("/api/jobs", response_model=PaginatedJobsResponse, tags=["Jobs"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_jobs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get paginated list of scraping jobs."""
    query = db.query(ScrapingJob)
    
    if status:
        query = query.filter(ScrapingJob.status == status)
    if keyword:
        query = query.filter(ScrapingJob.keyword.ilike(f"%{keyword}%"))
    
    total = query.count()
    total_pages = ceil(total / page_size)
    
    jobs = query.order_by(ScrapingJob.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    items = []
    for job in jobs:
        progress = round((job.completed_tasks or 0) / max(job.total_tasks or 1, 1) * 100, 1)
        items.append({
            "job_id": job.job_id,
            "keyword": job.keyword,
            "location": job.location,
            "radius": job.radius,
            "grid_size": job.grid_size,
            "status": job.status,
            "total_tasks": job.total_tasks or 0,
            "completed_tasks": job.completed_tasks or 0,
            "failed_tasks": job.failed_tasks or 0,
            "leads_found": job.leads_found or 0,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "progress_percent": progress
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@app.get("/api/jobs/{job_id}", response_model=JobDetailResponse, tags=["Jobs"])
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job details."""
    job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    progress = round((job.completed_tasks or 0) / max(job.total_tasks or 1, 1) * 100, 1)
    
    return {
        "job_id": job.job_id,
        "keyword": job.keyword,
        "location": job.location,
        "radius": job.radius,
        "grid_size": job.grid_size,
        "status": job.status,
        "total_tasks": job.total_tasks or 0,
        "completed_tasks": job.completed_tasks or 0,
        "failed_tasks": job.failed_tasks or 0,
        "leads_found": job.leads_found or 0,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "progress_percent": progress
    }


@app.delete("/api/jobs/{job_id}", response_model=MessageResponse, tags=["Jobs"])
async def delete_job(
    job_id: str, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Delete a scraping job."""
    job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()
    logger.info(f"Deleted job {job_id}")
    return {"message": f"Job {job_id} deleted", "success": True}


@app.post("/api/jobs/{job_id}/cancel", response_model=MessageResponse, tags=["Jobs"])
async def cancel_job(
    job_id: str, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Cancel a running job."""
    job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status in ["running", "pending"]:
        job.status = "cancelled"
        job.error_message = "Cancelled by user"
        db.commit()
        
        # Log cancellation
        log_entry = JobLog(job_id=job_id, level="INFO", message="Job cancelled by user")
        db.add(log_entry)
        db.commit()
        
        return {"message": f"Job {job_id} cancelled", "success": True}
    else:
        return {"message": f"Job is not running (current: {job.status})", "success": False}


@app.post("/api/jobs/{job_id}/restart", response_model=MessageResponse, tags=["Jobs"])
async def restart_job(
    job_id: str, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Restart a failed or cancelled job."""
    job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if USE_REDIS and q_discovery:
        job.status = "running"
        job.completed_tasks = 0
        job.failed_tasks = 0
        job.error_message = None
        db.commit()
        
        coordinates = generate_grid(job.location, job.radius, job.grid_size)
        for lat, lng in coordinates:
            q_discovery.enqueue('tasks.run_discovery', job_id, job.keyword, lat, lng)
        
        return {"message": f"Job {job_id} restarted", "success": True}
    else:
        return {"message": "Redis not available", "success": False}


# Leads endpoints


@app.get("/api/leads", response_model=PaginatedLeadsResponse, tags=["Leads"])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_leads(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    lead_type: Optional[str] = Query(None, description="Filter by lead type"),
    min_score: Optional[int] = Query(None, ge=0, le=10),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by name, phone, or address"),
    exclude_blacklisted: bool = Query(True),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get paginated list of leads with filtering."""
    # Use joinedload to prevent N+1 queries
    query = db.query(Business)\
        .outerjoin(LeadAnalysis, Business.id == LeadAnalysis.business_id)\
        .options(joinedload(Business.analysis))
    
    # Apply filters
    if lead_type:
        query = query.filter(LeadAnalysis.lead_type == lead_type)
    if min_score is not None:
        query = query.filter(LeadAnalysis.lead_score >= min_score)
    if category:
        query = query.filter(Business.category.ilike(f"%{category}%"))
    if status:
        query = query.filter(Business.status == status)
    if search:
        search_filter = or_(
            Business.name.ilike(f"%{search}%"),
            Business.phone.ilike(f"%{search}%"),
            Business.address.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    if exclude_blacklisted:
        query = query.filter(Business.is_blacklisted == False)
    
    # Get total count
    total = query.count()
    total_pages = ceil(total / page_size)
    
    # Get paginated results
    businesses = query.order_by(Business.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    items = []
    for biz in businesses:
        items.append({
            "id": biz.id,
            "place_id": biz.place_id,
            "name": biz.name,
            "phone": biz.phone,
            "website": biz.website,
            "rating": biz.rating,
            "reviews": biz.reviews,
            "category": biz.category,
            "address": biz.address,
            "maps_url": biz.maps_url,
            "tags": biz.tags,
            "notes": biz.notes,
            "status": biz.status,
            "is_blacklisted": biz.is_blacklisted,
            "type": biz.analysis.lead_type if biz.analysis else "UNKNOWN",
            "score": biz.analysis.lead_score if biz.analysis else 0,
            "created_at": biz.created_at
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


@app.get("/api/leads/{lead_id:int}", response_model=LeadResponse, tags=["Leads"])
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a single lead by ID."""
    biz = db.query(Business)\
        .options(joinedload(Business.analysis))\
        .filter(Business.id == lead_id).first()
    
    if not biz:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {
        "id": biz.id,
        "place_id": biz.place_id,
        "name": biz.name,
        "phone": biz.phone,
        "website": biz.website,
        "rating": biz.rating,
        "reviews": biz.reviews,
        "category": biz.category,
        "address": biz.address,
        "maps_url": biz.maps_url,
        "tags": biz.tags,
        "notes": biz.notes,
        "status": biz.status,
        "is_blacklisted": biz.is_blacklisted,
        "type": biz.analysis.lead_type if biz.analysis else "UNKNOWN",
        "score": biz.analysis.lead_score if biz.analysis else 0,
        "created_at": biz.created_at
    }


@app.patch("/api/leads/{lead_id:int}", response_model=LeadResponse, tags=["Leads"])
async def update_lead(
    lead_id: int, 
    update: LeadUpdate, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Update a lead's status, tags, or notes."""
    biz = db.query(Business).filter(Business.id == lead_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if update.status is not None:
        biz.status = update.status.value
    if update.tags is not None:
        biz.tags = update.tags
    if update.notes is not None:
        biz.notes = update.notes
    if update.is_blacklisted is not None:
        biz.is_blacklisted = update.is_blacklisted
    
    db.commit()
    db.refresh(biz)
    
    return await get_lead(lead_id, db)


@app.delete("/api/leads/{lead_id:int}", response_model=MessageResponse, tags=["Leads"])
async def delete_lead(
    lead_id: int, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Delete a lead."""
    biz = db.query(Business).filter(Business.id == lead_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    db.delete(biz)
    db.commit()
    return {"message": f"Lead {lead_id} deleted", "success": True}


# Bulk operations
@app.post("/api/leads/bulk-update", response_model=MessageResponse, tags=["Leads"])
async def bulk_update_leads(
    update: BulkLeadUpdate, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Update multiple leads at once."""
    updated_count = 0
    for lead_id in update.lead_ids:
        biz = db.query(Business).filter(Business.id == lead_id).first()
        if biz:
            if update.status is not None:
                biz.status = update.status.value
            if update.tags is not None:
                biz.tags = update.tags
            if update.is_blacklisted is not None:
                biz.is_blacklisted = update.is_blacklisted
            updated_count += 1
    
    db.commit()
    return {"message": f"Updated {updated_count} leads", "success": True}


@app.post("/api/leads/bulk-delete", response_model=MessageResponse, tags=["Leads"])
async def bulk_delete_leads(
    request: BulkDeleteRequest, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Delete multiple leads at once."""
    deleted_count = db.query(Business)\
        .filter(Business.id.in_(request.lead_ids))\
        .delete(synchronize_session=False)
    db.commit()
    return {"message": f"Deleted {deleted_count} leads", "success": True}


# Export
@app.get("/api/leads/export", tags=["Leads"])
@limiter.limit("5/minute")
async def export_leads(
    request: Request,
    lead_type: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Export leads as CSV file."""
    query = db.query(Business, LeadAnalysis)\
        .outerjoin(LeadAnalysis, Business.id == LeadAnalysis.business_id)\
        .filter(Business.is_blacklisted == False)
    
    if lead_type:
        query = query.filter(LeadAnalysis.lead_type == lead_type)
    if min_score is not None:
        query = query.filter(LeadAnalysis.lead_score >= min_score)
    if status:
        query = query.filter(Business.status == status)
    if category:
        query = query.filter(Business.category.ilike(f"%{category}%"))
    
    results = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "ID", "Business Name", "Phone", "Website", "Rating", "Reviews", 
        "Category", "Address", "Google Maps Link", "Lead Type", 
        "Lead Score", "Status", "Tags", "Notes"
    ])
    
    for biz, analysis in results:
        writer.writerow([
            biz.id,
            biz.name,
            biz.phone or "",
            biz.website or "",
            biz.rating or "",
            biz.reviews or "",
            biz.category or "",
            biz.address or "",
            biz.maps_url or "",
            analysis.lead_type if analysis else "UNKNOWN",
            analysis.lead_score if analysis else 0,
            biz.status,
            biz.tags or "",
            biz.notes or ""
        ])
    
    output.seek(0)
    filename = f"leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# Blacklist endpoints
@app.get("/api/blacklist", tags=["Blacklist"])
async def get_blacklist(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get blacklisted entries."""
    total = db.query(Blacklist).count()
    items = db.query(Blacklist)\
        .order_by(Blacklist.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    return {
        "items": [{"id": bl.id, "value": bl.value, "type": bl.type, "reason": bl.reason, "created_at": bl.created_at} for bl in items],
        "total": total,
        "page": page
    }


@app.post("/api/blacklist", response_model=MessageResponse, tags=["Blacklist"])
async def add_to_blacklist(
    entry: BlacklistCreate, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Add entry to blacklist."""
    existing = db.query(Blacklist).filter(Blacklist.value == entry.value).first()
    if existing:
        raise HTTPException(status_code=400, detail="Entry already blacklisted")
    
    bl = Blacklist(value=entry.value, type=entry.type, reason=entry.reason)
    db.add(bl)
    
    # If it's a phone, also mark matching businesses
    if entry.type == "phone":
        db.query(Business).filter(Business.phone == entry.value).update({"is_blacklisted": True})
    elif entry.type == "place_id":
        db.query(Business).filter(Business.place_id == entry.value).update({"is_blacklisted": True})
    
    db.commit()
    return {"message": f"Added {entry.value} to blacklist", "success": True}


@app.delete("/api/blacklist/{blacklist_id}", response_model=MessageResponse, tags=["Blacklist"])
async def remove_from_blacklist(
    blacklist_id: int, 
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Remove entry from blacklist."""
    bl = db.query(Blacklist).filter(Blacklist.id == blacklist_id).first()
    if not bl:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")
    
    # Unmark matching businesses
    if bl.type == "phone":
        db.query(Business).filter(Business.phone == bl.value).update({"is_blacklisted": False})
    elif bl.type == "place_id":
        db.query(Business).filter(Business.place_id == bl.value).update({"is_blacklisted": False})
    
    db.delete(bl)
    db.commit()
    return {"message": f"Removed {bl.value} from blacklist", "success": True}


# Stats endpoints
@app.get("/api/stats", response_model=StatsResponse, tags=["Stats"])
async def get_stats(db: Session = Depends(get_db), _: bool = Depends(verify_api_key)):
    """Get basic dashboard statistics."""
    # Check cache
    global stats_cache
    if stats_cache["data"] and stats_cache["expires"] and datetime.now() < stats_cache["expires"]:
        return stats_cache["data"]
    
    total_businesses = db.query(Business).filter(Business.is_blacklisted == False).count()
    qualified_leads = db.query(LeadAnalysis).filter(
        LeadAnalysis.lead_score >= settings.qualified_lead_min_score
    ).count()
    no_website_leads = db.query(LeadAnalysis).filter(LeadAnalysis.lead_type == "NO_WEBSITE").count()
    active_jobs = db.query(ScrapingJob).filter(ScrapingJob.status == "running").count()
    completed_jobs = db.query(ScrapingJob).filter(ScrapingJob.status == "completed").count()
    
    data = {
        "totalBusinesses": total_businesses,
        "qualifiedLeads": qualified_leads,
        "noWebsiteLeads": no_website_leads,
        "activeJobs": active_jobs,
        "completedJobs": completed_jobs
    }
    
    # Update cache
    stats_cache["data"] = data
    stats_cache["expires"] = datetime.now() + timedelta(seconds=STATS_CACHE_TTL)
    
    return data


@app.get("/api/stats/advanced", response_model=AdvancedStatsResponse, tags=["Stats"])
async def get_advanced_stats(db: Session = Depends(get_db), _: bool = Depends(verify_api_key)):
    """Get detailed statistics for dashboard charts."""
    # Lead type distribution
    lead_type_counts = db.query(
        LeadAnalysis.lead_type,
        func.count(LeadAnalysis.business_id)
    ).group_by(LeadAnalysis.lead_type).all()
    
    lead_types = {lt: count for lt, count in lead_type_counts}
    
    # Score distribution (single query instead of N+1)
    score_counts = db.query(
        LeadAnalysis.lead_score,
        func.count(LeadAnalysis.business_id)
    ).group_by(LeadAnalysis.lead_score).all()
    score_map = {s: c for s, c in score_counts}
    score_distribution = [{"score": s, "count": score_map.get(s, 0)} for s in range(9)]
    
    # Status distribution
    status_counts = db.query(
        Business.status,
        func.count(Business.id)
    ).filter(Business.is_blacklisted == False).group_by(Business.status).all()
    status_distribution = {s: c for s, c in status_counts}
    
    # Top categories
    category_counts = db.query(
        Business.category,
        func.count(Business.id)
    ).filter(Business.category.isnot(None), Business.is_blacklisted == False)\
     .group_by(Business.category)\
     .order_by(func.count(Business.id).desc())\
     .limit(10).all()
    
    top_categories = [{"category": cat or "Unknown", "count": count} for cat, count in category_counts]
    
    # High value leads
    high_value_leads = db.query(Business, LeadAnalysis)\
        .join(LeadAnalysis, Business.id == LeadAnalysis.business_id)\
        .filter(LeadAnalysis.lead_score >= 6, Business.is_blacklisted == False)\
        .order_by(LeadAnalysis.lead_score.desc())\
        .limit(5).all()
    
    top_leads = [{
        "id": biz.id,
        "name": biz.name,
        "category": biz.category,
        "phone": biz.phone,
        "rating": biz.rating,
        "type": analysis.lead_type,
        "score": analysis.lead_score
    } for biz, analysis in high_value_leads]
    
    # Recent jobs
    recent_jobs = db.query(ScrapingJob)\
        .order_by(ScrapingJob.created_at.desc())\
        .limit(5).all()
    
    jobs_progress = [{
        "job_id": job.job_id,
        "keyword": job.keyword,
        "location": job.location,
        "status": job.status,
        "progress": round((job.completed_tasks or 0) / max(job.total_tasks or 1, 1) * 100, 1),
        "leads_found": job.leads_found or 0
    } for job in recent_jobs]
    
    # Average rating
    avg_rating = db.query(func.avg(Business.rating))\
        .filter(Business.rating.isnot(None), Business.is_blacklisted == False)\
        .scalar() or 0
    
    return {
        "leadTypeDistribution": {
            "NO_WEBSITE": lead_types.get("NO_WEBSITE", 0),
            "WEBSITE_REDESIGN": lead_types.get("WEBSITE_REDESIGN", 0),
            "NORMAL": lead_types.get("NORMAL", 0)
        },
        "scoreDistribution": score_distribution,
        "topCategories": top_categories,
        "topLeads": top_leads,
        "recentJobs": jobs_progress,
        "averageRating": round(avg_rating, 1),
        "statusDistribution": status_distribution
    }


# Seed endpoint (for development)
@app.post("/api/seed", response_model=MessageResponse, tags=["Admin"])
async def seed_demo_data(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Seed the database with demo data."""
    from seed import seed_demo_data as run_seed
    try:
        result = run_seed()
        return {"message": result.get("message", "Seeded"), "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Job logs endpoint
@app.get("/api/jobs/{job_id}/logs", tags=["Jobs"])
async def get_job_logs(
    job_id: str,
    level: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get logs for a specific job."""
    query = db.query(JobLog).filter(JobLog.job_id == job_id)
    if level:
        query = query.filter(JobLog.level == level)
    
    logs = query.order_by(JobLog.created_at.desc()).limit(limit).all()
    
    return {
        "job_id": job_id,
        "logs": [{
            "id": log.id,
            "level": log.level,
            "message": log.message,
            "details": log.details,
            "created_at": log.created_at
        } for log in logs]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
