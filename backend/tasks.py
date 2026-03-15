"""
RQ Task Queue Workers with retry mechanism and improved error handling.
"""

import asyncio
import logging
import json
import time
import random
from functools import wraps
from database import SessionLocal
from models import Business, LeadAnalysis, ScrapingJob, Blacklist, JobLog
from discovery_scraper import scrape_google_maps_grid
from detail_fetcher import fetch_place_details
from website_analyzer import analyze_website, calculate_lead_score, determine_lead_type
from redis import Redis
from rq import Queue, get_current_job, Retry
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis connection
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
q_details = Queue('details', connection=redis_conn)
q_analysis = Queue('analysis', connection=redis_conn)

# Retry configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAYS = [60, 300, 900]  # 1 min, 5 min, 15 min


def retry_with_backoff(func):
    """Decorator for retry with exponential backoff."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        job = get_current_job()
        retry_count = job.meta.get('retry_count', 0) if job else 0
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if retry_count < MAX_RETRIES:
                delay = RETRY_DELAYS[min(retry_count, len(RETRY_DELAYS) - 1)]
                # Add jitter to prevent thundering herd
                delay += random.uniform(0, delay * 0.1)
                
                logger.warning(f"Retry {retry_count + 1}/{MAX_RETRIES} for {func.__name__} in {delay}s: {e}")
                
                if job:
                    job.meta['retry_count'] = retry_count + 1
                    job.save_meta()
                
                raise  # Let RQ handle the retry
            else:
                logger.error(f"Max retries exceeded for {func.__name__}: {e}")
                raise
    return wrapper


def log_to_job(job_id: str, level: str, message: str, details: dict = None):
    """Log a message to the job_logs table."""
    db = SessionLocal()
    try:
        log_entry = JobLog(
            job_id=job_id,
            level=level,
            message=message,
            details=json.dumps(details) if details else None
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log to job {job_id}: {e}")
    finally:
        db.close()


def update_job_status(job_id: str, status: str, error_message: str = None):
    """Update the status of a scraping job."""
    db = SessionLocal()
    try:
        job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            db.commit()
            logger.info(f"Job {job_id} status updated to {status}")
    except Exception as e:
        logger.error(f"Error updating job status: {e}")
    finally:
        db.close()


def increment_job_progress(job_id: str, new_leads: int = 0, failed: bool = False):
    """Increment job progress and check if completed."""
    db = SessionLocal()
    try:
        job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
        if job:
            if job.status == "cancelled":
                logger.info(f"Job {job_id} was cancelled, skipping progress update")
                return False
            
            if failed:
                job.failed_tasks = (job.failed_tasks or 0) + 1
            else:
                job.completed_tasks = (job.completed_tasks or 0) + 1
            
            job.leads_found = (job.leads_found or 0) + new_leads
            
            # Check if all tasks are completed
            total_done = (job.completed_tasks or 0) + (job.failed_tasks or 0)
            if job.total_tasks > 0 and total_done >= job.total_tasks:
                if job.failed_tasks > 0 and job.failed_tasks == job.total_tasks:
                    job.status = "failed"
                    job.error_message = "All tasks failed"
                else:
                    job.status = "completed"
                logger.info(f"Job {job_id} finished! Status: {job.status}, Found: {job.leads_found}")
            
            db.commit()
            logger.info(f"Job {job_id} progress: {job.completed_tasks}/{job.total_tasks} (failed: {job.failed_tasks})")
            return True
    except Exception as e:
        logger.error(f"Error updating job progress: {e}")
    finally:
        db.close()
    return False


def is_blacklisted(db, place_id: str = None, phone: str = None) -> bool:
    """Check if a place_id or phone is blacklisted."""
    if place_id:
        if db.query(Blacklist).filter(Blacklist.value == place_id, Blacklist.type == "place_id").first():
            return True
    if phone:
        if db.query(Blacklist).filter(Blacklist.value == phone, Blacklist.type == "phone").first():
            return True
    return False


@retry_with_backoff
def run_discovery(job_id: str, keyword: str, lat: float, lng: float):
    """
    Stage 1: Discover businesses from Google Maps for a specific coordinate.
    """
    logger.info(f"[Discovery] Starting for job {job_id}: {keyword} at ({lat}, {lng})")
    
    # Check if job is cancelled
    db = SessionLocal()
    try:
        job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
        if job and job.status == "cancelled":
            logger.info(f"[Discovery] Job {job_id} cancelled, skipping")
            return {"job_id": job_id, "status": "cancelled"}
    finally:
        db.close()
    
    try:
        # Run async playwright in sync RQ worker
        loop = asyncio.new_event_loop()
        try:
            results = loop.run_until_complete(scrape_google_maps_grid(keyword, lat, lng))
        finally:
            loop.close()
        logger.info(f"[Discovery] Found {len(results)} businesses at ({lat}, {lng})")
        
        db = SessionLocal()
        new_count = 0
        skipped_count = 0
        
        try:
            for res in results:
                try:
                    # Check blacklist
                    if is_blacklisted(db, place_id=res['place_id']):
                        skipped_count += 1
                        continue
                    
                    # Deduplication check
                    exists = db.query(Business).filter(Business.place_id == res['place_id']).first()
                    if not exists:
                        new_biz = Business(
                            place_id=res['place_id'],
                            name=res['name'],
                            maps_url=res['maps_url'],
                            lat=res['lat'],
                            lng=res['lng'],
                            source_job_id=job_id,
                            status="new"
                        )
                        db.add(new_biz)
                        db.commit()
                        db.refresh(new_biz)
                        new_count += 1
                        
                        # Queue next stage with retry
                        q_details.enqueue(
                            run_details_fetch, 
                            new_biz.id, 
                            new_biz.maps_url,
                            retry=Retry(max=MAX_RETRIES, interval=RETRY_DELAYS)
                        )
                        logger.info(f"[Discovery] Queued details fetch for: {new_biz.name}")
                except Exception as e:
                    logger.error(f"[Discovery] Error saving business: {e}")
                    db.rollback()
        finally:
            db.close()
        
        # Log progress
        log_to_job(job_id, "INFO", f"Discovery completed at ({lat}, {lng})", {
            "found": len(results),
            "new": new_count,
            "skipped": skipped_count
        })
        
        # Update job progress
        increment_job_progress(job_id, new_count)
        
        logger.info(f"[Discovery] Completed: {new_count} new, {skipped_count} skipped")
        return {"job_id": job_id, "new_businesses": new_count}
        
    except Exception as e:
        logger.error(f"[Discovery] Error: {e}")
        log_to_job(job_id, "ERROR", f"Discovery failed at ({lat}, {lng})", {"error": str(e)})
        increment_job_progress(job_id, 0, failed=True)
        raise


@retry_with_backoff
def run_details_fetch(business_id: int, maps_url: str):
    """
    Stage 2: Fetch detailed business information from the Maps page.
    """
    logger.info(f"[Details] Fetching details for business {business_id}")
    
    try:
        loop = asyncio.new_event_loop()
        try:
            details = loop.run_until_complete(fetch_place_details(maps_url))
        finally:
            loop.close()
        
        db = SessionLocal()
        try:
            biz = db.query(Business).filter(Business.id == business_id).first()
            
            if biz:
                # Check if phone is blacklisted
                if details.get('phone') and is_blacklisted(db, phone=details.get('phone')):
                    biz.is_blacklisted = True
                    db.commit()
                    logger.info(f"[Details] Business {biz.name} blacklisted by phone")
                    return {"business_id": business_id, "blacklisted": True}
                
                # Phone deduplication - check if another business has same phone
                if details.get('phone'):
                    existing_with_phone = db.query(Business).filter(
                        Business.phone == details.get('phone'),
                        Business.id != business_id
                    ).first()
                    if existing_with_phone:
                        logger.info(f"[Details] Phone duplicate found, skipping: {details.get('phone')}")
                        # Don't save phone, but continue with other details
                        details['phone'] = None
                
                biz.website = details.get('website')
                biz.phone = details.get('phone')
                biz.rating = details.get('rating')
                biz.reviews = details.get('reviews')
                biz.category = details.get('category')
                biz.address = details.get('address')
                db.commit()
                
                logger.info(f"[Details] Updated: {biz.name} - Website: {biz.website}, Phone: {biz.phone}")
                
                # Queue next stage with retry
                q_analysis.enqueue(
                    run_analysis, 
                    business_id, 
                    details.get('website'), 
                    details.get('rating'), 
                    details.get('reviews'), 
                    details.get('phone'),
                    retry=Retry(max=MAX_RETRIES, interval=RETRY_DELAYS)
                )
        finally:
            db.close()
        
        return {"business_id": business_id, "website": details.get('website')}
        
    except Exception as e:
        logger.error(f"[Details] Error fetching details for {business_id}: {e}")
        raise


@retry_with_backoff
def run_analysis(business_id: int, website: str, rating: float, reviews: int, phone: str):
    """
    Stage 3: Analyze the business website and score the lead.
    """
    logger.info(f"[Analysis] Analyzing business {business_id}")
    
    try:
        loop = asyncio.new_event_loop()
        try:
            analysis_data = loop.run_until_complete(analyze_website(website))
        finally:
            loop.close()
        
        db = SessionLocal()
        try:
            has_website = bool(website)
            score = calculate_lead_score(has_website, rating, reviews, bool(phone))
            lead_type = determine_lead_type(has_website, analysis_data['mobile_friendly'])
            
            # Check if analysis already exists (upsert)
            existing = db.query(LeadAnalysis).filter(LeadAnalysis.business_id == business_id).first()
            if existing:
                existing.lead_type = lead_type
                existing.lead_score = score
                existing.ssl_enabled = analysis_data['ssl_enabled']
                existing.mobile_friendly = analysis_data['mobile_friendly']
                existing.load_time = analysis_data['load_time']
            else:
                analysis = LeadAnalysis(
                    business_id=business_id,
                    lead_type=lead_type,
                    lead_score=score,
                    ssl_enabled=analysis_data['ssl_enabled'],
                    mobile_friendly=analysis_data['mobile_friendly'],
                    load_time=analysis_data['load_time']
                )
                db.add(analysis)
            
            db.commit()
            logger.info(f"[Analysis] Scored: business {business_id}, type={lead_type}, score={score}")
            
            # Optionally send Telegram notification for high-value leads
            if score >= 6 and lead_type == "NO_WEBSITE":
                try:
                    from telegram_bot import notify_high_value_lead
                    biz = db.query(Business).filter(Business.id == business_id).first()
                    if biz:
                        notify_loop = asyncio.new_event_loop()
                        try:
                            notify_loop.run_until_complete(notify_high_value_lead({
                                "name": biz.name,
                                "phone": biz.phone,
                                "website": biz.website,
                                "rating": biz.rating,
                                "reviews": biz.reviews,
                                "address": biz.address,
                                "type": lead_type,
                                "score": score
                            }))
                        finally:
                            notify_loop.close()
                except Exception as e:
                    logger.warning(f"[Analysis] Failed to send Telegram notification: {e}")
        finally:
            db.close()
        
        return {"business_id": business_id, "lead_type": lead_type, "score": score}
        
    except Exception as e:
        logger.error(f"[Analysis] Error analyzing business {business_id}: {e}")
        raise


def cleanup_cancelled_jobs():
    """Cleanup task: mark old running jobs as failed if no progress."""
    logger.info("[Cleanup] Checking for stale jobs...")
    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        stale_threshold = datetime.now() - timedelta(hours=6)
        
        stale_jobs = db.query(ScrapingJob).filter(
            ScrapingJob.status == "running",
            ScrapingJob.updated_at < stale_threshold
        ).all()
        
        for job in stale_jobs:
            job.status = "failed"
            job.error_message = "Job stalled - no progress for 6 hours"
            log_to_job(job.job_id, "ERROR", "Job marked as failed due to inactivity")
        
        db.commit()
        logger.info(f"[Cleanup] Marked {len(stale_jobs)} stale jobs as failed")
    except Exception as e:
        logger.error(f"[Cleanup] Error: {e}")
    finally:
        db.close()
