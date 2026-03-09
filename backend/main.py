from fastapi import FastAPI, Depends, BackgroundTasks, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import engine, Base, get_db
from models import ScrapingJob, Business, LeadAnalysis, DemoSite
from schemas import JobCreate, JobResponse
from grid_generator import generate_grid
import uuid
import os
import csv
import io
from typing import Optional

# Optional Redis support - works without it for local dev
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
redis_conn = None
q_discovery = None

if USE_REDIS:
    try:
        from redis import Redis
        from rq import Queue
        redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        q_discovery = Queue('discovery', connection=redis_conn)
    except Exception as e:
        print(f"Redis not available: {e}")
        USE_REDIS = False

# Create DB Tables
Base.metadata.create_all(bind=engine)

# Create demo_sites directory
os.makedirs("demo_sites", exist_ok=True)

app = FastAPI(title="Lead Engine API", description="Automated Lead Generation System")

# Serve demo sites as static files
app.mount("/demo-sites", StaticFiles(directory="demo_sites"), name="demo_sites")

# Allow Next.js frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, change to your Next.js domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/jobs", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    job_id = f"JOB-{str(uuid.uuid4())[:8].upper()}"
    
    new_job = ScrapingJob(
        job_id=job_id,
        keyword=job.keyword,
        location=job.location,
        radius=job.radius,
        grid_size=job.grid_size,
        status="pending" if not USE_REDIS else "running"
    )
    db.add(new_job)
    db.commit()
    
    # Generate Grid and Queue Discovery Tasks (only if Redis is available)
    if USE_REDIS and q_discovery:
        coordinates = generate_grid(job.location, job.radius, job.grid_size)
        for lat, lng in coordinates:
            # Enqueue the task in RQ
            q_discovery.enqueue('tasks.run_discovery', job_id, job.keyword, lat, lng)
        
    return {"job_id": job_id, "status": new_job.status}

@app.get("/api/leads")
def get_leads(db: Session = Depends(get_db)):
    # Join Business, Analysis, and Demo tables
    results = db.query(Business, LeadAnalysis, DemoSite)\
        .outerjoin(LeadAnalysis, Business.id == LeadAnalysis.business_id)\
        .outerjoin(DemoSite, Business.id == DemoSite.business_id)\
        .all()
        
    leads = []
    for biz, analysis, demo in results:
        leads.append({
            "id": biz.id,
            "name": biz.name,
            "phone": biz.phone,
            "website": biz.website,
            "rating": biz.rating,
            "reviews": biz.reviews,
            "category": biz.category,
            "type": analysis.lead_type if analysis else "UNKNOWN",
            "score": analysis.lead_score if analysis else 0,
            "demoUrl": demo.demo_url if demo else None
        })
    return leads

@app.get("/api/jobs")
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(ScrapingJob).all()
    return [
        {
            "job_id": job.job_id,
            "keyword": job.keyword,
            "location": job.location,
            "radius": job.radius,
            "grid_size": job.grid_size,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None
        }
        for job in jobs
    ]

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_businesses = db.query(Business).count()
    qualified_leads = db.query(LeadAnalysis).filter(LeadAnalysis.lead_score >= 5).count()
    demo_sites = db.query(DemoSite).count()
    active_jobs = db.query(ScrapingJob).filter(ScrapingJob.status == "running").count()
    
    return {
        "totalBusinesses": total_businesses,
        "qualifiedLeads": qualified_leads,
        "demoSites": demo_sites,
        "activeJobs": active_jobs
    }

@app.post("/api/seed")
def seed_demo_data(db: Session = Depends(get_db)):
    """Seed the database with demo data for testing"""
    # Check if data already exists
    if db.query(Business).count() > 0:
        return {"message": "Data already exists"}
    
    # Demo businesses
    demo_businesses = [
        {"place_id": "demo1", "name": "Smile Dental Clinic", "phone": "+91 98765 43210", "website": None, "rating": 4.8, "reviews": 124, "category": "Dentist", "address": "Model Town, Ludhiana", "lat": 30.9, "lng": 75.85, "maps_url": "https://maps.google.com/1"},
        {"place_id": "demo2", "name": "City Gym & Fitness", "phone": "+91 87654 32109", "website": "http://citygym.com", "rating": 3.5, "reviews": 45, "category": "Gym", "address": "Sector 17, Chandigarh", "lat": 30.74, "lng": 76.79, "maps_url": "https://maps.google.com/2"},
        {"place_id": "demo3", "name": "Glamour Salon", "phone": "+91 76543 21098", "website": None, "rating": 4.2, "reviews": 89, "category": "Salon", "address": "Connaught Place, Delhi", "lat": 28.63, "lng": 77.22, "maps_url": "https://maps.google.com/3"},
        {"place_id": "demo4", "name": "Health First Clinic", "phone": "+91 65432 10987", "website": "https://healthfirst.in", "rating": 4.9, "reviews": 312, "category": "Clinic", "address": "Bandra, Mumbai", "lat": 19.05, "lng": 72.83, "maps_url": "https://maps.google.com/4"},
        {"place_id": "demo5", "name": "Bright Smiles", "phone": "+91 54321 09876", "website": "http://brightsmiles.com", "rating": 4.1, "reviews": 12, "category": "Dentist", "address": "Sarabha Nagar, Ludhiana", "lat": 30.87, "lng": 75.82, "maps_url": "https://maps.google.com/5"},
    ]
    
    for biz_data in demo_businesses:
        biz = Business(**biz_data)
        db.add(biz)
    db.commit()
    
    # Add analysis data
    analyses = [
        {"business_id": 1, "lead_type": "NO_WEBSITE", "lead_score": 7, "ssl_enabled": False, "mobile_friendly": False, "load_time": 0},
        {"business_id": 2, "lead_type": "WEBSITE_REDESIGN", "lead_score": 5, "ssl_enabled": False, "mobile_friendly": False, "load_time": 3.2},
        {"business_id": 3, "lead_type": "NO_WEBSITE", "lead_score": 6, "ssl_enabled": False, "mobile_friendly": False, "load_time": 0},
        {"business_id": 4, "lead_type": "NORMAL", "lead_score": 3, "ssl_enabled": True, "mobile_friendly": True, "load_time": 1.5},
        {"business_id": 5, "lead_type": "WEBSITE_REDESIGN", "lead_score": 4, "ssl_enabled": False, "mobile_friendly": False, "load_time": 4.1},
    ]
    
    for analysis_data in analyses:
        analysis = LeadAnalysis(**analysis_data)
        db.add(analysis)
    db.commit()
    
    # Add demo sites for high-score leads
    demo_sites = [
        {"business_id": 1, "demo_url": "/demo-sites/smile-dental-clinic-demo.html"},
        {"business_id": 3, "demo_url": "/demo-sites/glamour-salon-demo.html"},
    ]
    
    for demo_data in demo_sites:
        demo = DemoSite(**demo_data)
        db.add(demo)
    db.commit()
    
    # Add demo jobs
    demo_jobs = [
        {"job_id": "JOB-1029", "keyword": "Dentist", "location": "Ludhiana", "radius": 10, "grid_size": "10x10", "status": "completed"},
        {"job_id": "JOB-1030", "keyword": "Gym", "location": "Chandigarh", "radius": 15, "grid_size": "15x15", "status": "completed"},
    ]
    
    for job_data in demo_jobs:
        job = ScrapingJob(**job_data)
        db.add(job)
    db.commit()
    
    return {"message": "Demo data seeded successfully", "businesses": len(demo_businesses)}

@app.get("/api/leads/export")
def export_leads(
    lead_type: Optional[str] = Query(None, description="Filter by lead type: NO_WEBSITE, WEBSITE_REDESIGN, NORMAL"),
    min_score: Optional[int] = Query(None, description="Minimum lead score"),
    db: Session = Depends(get_db)
):
    """Export leads as CSV file"""
    query = db.query(Business, LeadAnalysis, DemoSite)\
        .outerjoin(LeadAnalysis, Business.id == LeadAnalysis.business_id)\
        .outerjoin(DemoSite, Business.id == DemoSite.business_id)
    
    if lead_type:
        query = query.filter(LeadAnalysis.lead_type == lead_type)
    if min_score:
        query = query.filter(LeadAnalysis.lead_score >= min_score)
    
    results = query.all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        "Business Name", "Phone", "Website", "Rating", "Reviews", 
        "Category", "Address", "Google Maps Link", "Lead Type", 
        "Lead Score", "Demo Site URL"
    ])
    
    # Data rows
    for biz, analysis, demo in results:
        writer.writerow([
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
            demo.demo_url if demo else ""
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"}
    )

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job details with lead count"""
    job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Count leads associated with this job (businesses found during this job)
    lead_count = db.query(Business).count()  # In production, filter by job_id
    
    return {
        "job_id": job.job_id,
        "keyword": job.keyword,
        "location": job.location,
        "radius": job.radius,
        "grid_size": job.grid_size,
        "status": job.status,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "leads_found": lead_count
    }

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a scraping job"""
    job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()
    return {"message": f"Job {job_id} deleted"}

@app.post("/api/jobs/{job_id}/restart")
def restart_job(job_id: str, db: Session = Depends(get_db)):
    """Restart a failed or pending job"""
    job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if USE_REDIS and q_discovery:
        job.status = "running"
        db.commit()
        
        coordinates = generate_grid(job.location, job.radius, job.grid_size)
        for lat, lng in coordinates:
            q_discovery.enqueue('tasks.run_discovery', job_id, job.keyword, lat, lng)
        
        return {"message": f"Job {job_id} restarted", "status": "running"}
    else:
        return {"message": "Redis not available. Cannot restart job.", "status": job.status}

@app.get("/api/leads/{lead_id}")
def get_lead_details(lead_id: int, db: Session = Depends(get_db)):
    """Get detailed lead information"""
    biz = db.query(Business).filter(Business.id == lead_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    analysis = db.query(LeadAnalysis).filter(LeadAnalysis.business_id == lead_id).first()
    demo = db.query(DemoSite).filter(DemoSite.business_id == lead_id).first()
    
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
        "lat": biz.lat,
        "lng": biz.lng,
        "maps_url": biz.maps_url,
        "created_at": biz.created_at.isoformat() if biz.created_at else None,
        "analysis": {
            "lead_type": analysis.lead_type if analysis else "UNKNOWN",
            "lead_score": analysis.lead_score if analysis else 0,
            "ssl_enabled": analysis.ssl_enabled if analysis else False,
            "mobile_friendly": analysis.mobile_friendly if analysis else False,
            "load_time": analysis.load_time if analysis else None
        },
        "demo_url": demo.demo_url if demo else None
    }

@app.post("/api/leads/{lead_id}/generate-demo")
def generate_demo_for_lead(lead_id: int, db: Session = Depends(get_db)):
    """Manually generate a demo site for a lead"""
    biz = db.query(Business).filter(Business.id == lead_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Check if demo already exists
    existing_demo = db.query(DemoSite).filter(DemoSite.business_id == lead_id).first()
    if existing_demo:
        return {"message": "Demo already exists", "demo_url": existing_demo.demo_url}
    
    from demo_generator import generate_demo_site
    demo_url = generate_demo_site(biz.name, biz.category or "Business")
    
    demo = DemoSite(business_id=lead_id, demo_url=demo_url)
    db.add(demo)
    db.commit()
    
    return {"message": "Demo generated", "demo_url": demo_url}

@app.get("/api/queue/status")
def get_queue_status():
    """Get status of all queues (requires Redis)"""
    if not USE_REDIS or not redis_conn:
        return {"error": "Redis not available", "queues": {}}
    
    from rq import Queue
    queues = {}
    for queue_name in ['discovery', 'details', 'analysis', 'demo']:
        q = Queue(queue_name, connection=redis_conn)
        queues[queue_name] = {
            "pending": len(q),
            "failed": q.failed_job_registry.count,
            "finished": q.finished_job_registry.count
        }
    
    return {"queues": queues}

@app.get("/")
def root():
    """API Health check"""
    return {
        "status": "running",
        "api": "Lead Engine API",
        "redis": USE_REDIS,
        "docs": "/docs"
    }

# ============== TELEGRAM ENDPOINTS ==============
import asyncio
from telegram_bot import (
    send_telegram_message, 
    export_leads_to_telegram,
    send_daily_summary,
    notify_high_value_lead
)

@app.post("/api/telegram/test")
async def test_telegram():
    """Test Telegram connection by sending a test message."""
    result = await send_telegram_message("🚀 Lead Engine connected successfully!")
    if result:
        return {"status": "success", "message": "Test message sent to Telegram"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Telegram message. Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")

@app.post("/api/telegram/export")
async def export_to_telegram(
    min_score: int = Query(0, description="Minimum score filter"),
    type_filter: Optional[str] = Query(None, description="Filter by type: NO_WEBSITE, OUTDATED, etc"),
    db: Session = Depends(get_db)
):
    """Export leads as CSV to Telegram."""
    query = db.query(Business)
    
    if min_score > 0:
        query = query.filter(Business.score >= min_score)
    if type_filter:
        query = query.filter(Business.type == type_filter)
    
    businesses = query.order_by(Business.score.desc()).all()
    
    leads = []
    for b in businesses:
        leads.append({
            "name": b.name,
            "phone": b.phone,
            "website": b.website,
            "rating": b.rating,
            "reviews": b.reviews,
            "type": b.type,
            "score": b.score,
            "address": b.address
        })
    
    if not leads:
        raise HTTPException(status_code=404, detail="No leads found matching criteria")
    
    result = await export_leads_to_telegram(leads)
    if result:
        return {"status": "success", "message": f"Exported {len(leads)} leads to Telegram"}
    else:
        raise HTTPException(status_code=500, detail="Failed to export to Telegram")

@app.post("/api/telegram/notify-lead/{lead_id}")
async def notify_lead_telegram(lead_id: int, db: Session = Depends(get_db)):
    """Send a specific lead to Telegram."""
    business = db.query(Business).filter(Business.id == lead_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead_data = {
        "name": business.name,
        "phone": business.phone,
        "website": business.website,
        "rating": business.rating,
        "reviews": business.reviews,
        "type": business.type,
        "score": business.score,
        "address": business.address,
        "demo_url": business.demo_url
    }
    
    result = await notify_high_value_lead(lead_data, min_score=0)
    if result:
        return {"status": "success", "message": "Lead sent to Telegram"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send to Telegram")

@app.post("/api/telegram/summary")
async def send_summary_telegram(db: Session = Depends(get_db)):
    """Send daily summary to Telegram."""
    stats = {
        "total": db.query(Business).count(),
        "with_phone": db.query(Business).filter(Business.phone.isnot(None)).count(),
        "no_website": db.query(Business).filter(Business.type == "NO_WEBSITE").count(),
        "high_score": db.query(Business).filter(Business.score >= 5).count(),
        "top_leads": []
    }
    
    top = db.query(Business).filter(
        Business.score >= 5
    ).order_by(Business.score.desc()).limit(5).all()
    
    for b in top:
        stats["top_leads"].append({
            "name": b.name,
            "phone": b.phone
        })
    
    result = await send_daily_summary(stats)
    if result:
        return {"status": "success", "message": "Summary sent to Telegram"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send summary")

