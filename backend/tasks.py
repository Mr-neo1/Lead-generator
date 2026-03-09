import asyncio
import logging
from database import SessionLocal
from models import Business, LeadAnalysis, DemoSite, ScrapingJob
from discovery_scraper import scrape_google_maps_grid
from detail_fetcher import fetch_place_details
from website_analyzer import analyze_website, calculate_lead_score, determine_lead_type
from demo_generator import generate_demo_site
from redis import Redis
from rq import Queue, get_current_job
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
q_details = Queue('details', connection=redis_conn)
q_analysis = Queue('analysis', connection=redis_conn)
q_demo = Queue('demo', connection=redis_conn)

def update_job_status(job_id: str, status: str):
    """Update the status of a scraping job"""
    db = SessionLocal()
    try:
        job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
        if job:
            job.status = status
            db.commit()
            logger.info(f"Job {job_id} status updated to {status}")
    except Exception as e:
        logger.error(f"Error updating job status: {e}")
    finally:
        db.close()

def run_discovery(job_id: str, keyword: str, lat: float, lng: float):
    """
    Stage 1: Discover businesses from Google Maps for a specific coordinate
    """
    logger.info(f"[Discovery] Starting for job {job_id}: {keyword} at ({lat}, {lng})")
    
    try:
        # Run async playwright in sync RQ worker
        results = asyncio.run(scrape_google_maps_grid(keyword, lat, lng))
        logger.info(f"[Discovery] Found {len(results)} businesses at ({lat}, {lng})")
        
        db = SessionLocal()
        new_count = 0
        
        for res in results:
            try:
                # Deduplication check
                exists = db.query(Business).filter(Business.place_id == res['place_id']).first()
                if not exists:
                    new_biz = Business(
                        place_id=res['place_id'],
                        name=res['name'],
                        maps_url=res['maps_url'],
                        lat=res['lat'],
                        lng=res['lng']
                    )
                    db.add(new_biz)
                    db.commit()
                    db.refresh(new_biz)
                    new_count += 1
                    
                    # Queue next stage
                    q_details.enqueue(run_details_fetch, new_biz.id, new_biz.maps_url)
                    logger.info(f"[Discovery] Queued details fetch for: {new_biz.name}")
            except Exception as e:
                logger.error(f"[Discovery] Error saving business: {e}")
                db.rollback()
                
        db.close()
        logger.info(f"[Discovery] Completed: {new_count} new businesses added")
        return {"job_id": job_id, "new_businesses": new_count}
        
    except Exception as e:
        logger.error(f"[Discovery] Error: {e}")
        raise

def run_details_fetch(business_id: int, maps_url: str):
    """
    Stage 2: Fetch detailed business information from the Maps page
    """
    logger.info(f"[Details] Fetching details for business {business_id}")
    
    try:
        details = asyncio.run(fetch_place_details(maps_url))
        db = SessionLocal()
        biz = db.query(Business).filter(Business.id == business_id).first()
        
        if biz:
            biz.website = details.get('website')
            biz.phone = details.get('phone')
            biz.rating = details.get('rating')
            biz.reviews = details.get('reviews')
            biz.category = details.get('category')
            biz.address = details.get('address')
            db.commit()
            
            logger.info(f"[Details] Updated: {biz.name} - Website: {biz.website}, Phone: {biz.phone}")
            
            # Queue next stage
            q_analysis.enqueue(
                run_analysis, 
                business_id, 
                details.get('website'), 
                details.get('rating'), 
                details.get('reviews'), 
                details.get('phone')
            )
        
        db.close()
        return {"business_id": business_id, "website": details.get('website')}
        
    except Exception as e:
        logger.error(f"[Details] Error fetching details for {business_id}: {e}")
        raise

def run_analysis(business_id: int, website: str, rating: float, reviews: int, phone: str):
    """
    Stage 3: Analyze the business website and score the lead
    """
    logger.info(f"[Analysis] Analyzing business {business_id}")
    
    try:
        analysis_data = asyncio.run(analyze_website(website))
        db = SessionLocal()
        
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
        
        # Demo generation disabled - uncomment below if you want auto-generated demo sites
        # if score >= 6:
        #     biz = db.query(Business).filter(Business.id == business_id).first()
        #     if biz:
        #         q_demo.enqueue(run_demo_generation, business_id, biz.name, biz.category)
        #         logger.info(f"[Analysis] Queued demo generation for high-score lead: {biz.name}")
        
        db.close()
        return {"business_id": business_id, "lead_type": lead_type, "score": score}
        
    except Exception as e:
        logger.error(f"[Analysis] Error analyzing business {business_id}: {e}")
        raise

def run_demo_generation(business_id: int, name: str, category: str):
    """
    Stage 4: Generate a demo website for high-priority leads
    """
    logger.info(f"[Demo] Generating demo for: {name}")
    
    try:
        db = SessionLocal()
        
        # Check if demo already exists
        existing = db.query(DemoSite).filter(DemoSite.business_id == business_id).first()
        if existing:
            logger.info(f"[Demo] Demo already exists for {name}")
            db.close()
            return {"business_id": business_id, "demo_url": existing.demo_url}
        
        demo_url = generate_demo_site(name, category or "Business")
        
        demo = DemoSite(business_id=business_id, demo_url=demo_url)
        db.add(demo)
        db.commit()
        
        logger.info(f"[Demo] Generated: {demo_url}")
        db.close()
        return {"business_id": business_id, "demo_url": demo_url}
        
    except Exception as e:
        logger.error(f"[Demo] Error generating demo for {name}: {e}")
        raise
