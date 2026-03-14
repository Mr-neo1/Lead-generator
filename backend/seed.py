"""
Database seed script for demo data.
Run: python seed.py
"""

from database import SessionLocal, init_db
from models import Business, LeadAnalysis, ScrapingJob, Blacklist
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_demo_data():
    """Seed the database with demo data for testing."""
    init_db()
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Business).count() > 0:
            logger.info("Data already exists, skipping seed")
            return {"message": "Data already exists"}
        
        # Demo businesses
        demo_businesses = [
            {
                "place_id": "demo1", 
                "name": "Smile Dental Clinic", 
                "phone": "+91 98765 43210", 
                "website": None, 
                "rating": 4.8, 
                "reviews": 124, 
                "category": "Dentist", 
                "address": "Model Town, Ludhiana", 
                "lat": 30.9, 
                "lng": 75.85, 
                "maps_url": "https://maps.google.com/1",
                "source_job_id": "JOB-DEMO1",
                "status": "new"
            },
            {
                "place_id": "demo2", 
                "name": "City Gym & Fitness", 
                "phone": "+91 87654 32109", 
                "website": "http://citygym.com", 
                "rating": 3.5, 
                "reviews": 45, 
                "category": "Gym", 
                "address": "Sector 17, Chandigarh", 
                "lat": 30.74, 
                "lng": 76.79, 
                "maps_url": "https://maps.google.com/2",
                "source_job_id": "JOB-DEMO1",
                "status": "contacted"
            },
            {
                "place_id": "demo3", 
                "name": "Glamour Salon", 
                "phone": "+91 76543 21098", 
                "website": None, 
                "rating": 4.2, 
                "reviews": 89, 
                "category": "Salon", 
                "address": "Connaught Place, Delhi", 
                "lat": 28.63, 
                "lng": 77.22, 
                "maps_url": "https://maps.google.com/3",
                "source_job_id": "JOB-DEMO2",
                "status": "new",
                "tags": "high-priority,follow-up"
            },
            {
                "place_id": "demo4", 
                "name": "Health First Clinic", 
                "phone": "+91 65432 10987", 
                "website": "https://healthfirst.in", 
                "rating": 4.9, 
                "reviews": 312, 
                "category": "Clinic", 
                "address": "Bandra, Mumbai", 
                "lat": 19.05, 
                "lng": 72.83, 
                "maps_url": "https://maps.google.com/4",
                "source_job_id": "JOB-DEMO2",
                "status": "qualified"
            },
            {
                "place_id": "demo5", 
                "name": "Bright Smiles", 
                "phone": "+91 54321 09876", 
                "website": "http://brightsmiles.com", 
                "rating": 4.1, 
                "reviews": 12, 
                "category": "Dentist", 
                "address": "Sarabha Nagar, Ludhiana", 
                "lat": 30.87, 
                "lng": 75.82, 
                "maps_url": "https://maps.google.com/5",
                "source_job_id": "JOB-DEMO1",
                "status": "new"
            },
            {
                "place_id": "demo6", 
                "name": "FitZone Studio", 
                "phone": "+91 43210 98765", 
                "website": None, 
                "rating": 4.6, 
                "reviews": 78, 
                "category": "Gym", 
                "address": "Jalandhar", 
                "lat": 31.32, 
                "lng": 75.57, 
                "maps_url": "https://maps.google.com/6",
                "source_job_id": "JOB-DEMO2",
                "status": "new",
                "notes": "Owner interested in website development"
            },
            {
                "place_id": "demo7", 
                "name": "Perfect Cuts Salon", 
                "phone": "+91 32109 87654", 
                "website": "http://perfectcuts.in", 
                "rating": 3.8, 
                "reviews": 34, 
                "category": "Salon", 
                "address": "Amritsar", 
                "lat": 31.63, 
                "lng": 74.87, 
                "maps_url": "https://maps.google.com/7",
                "source_job_id": "JOB-DEMO1",
                "status": "rejected"
            },
            {
                "place_id": "demo8", 
                "name": "Wellness Center", 
                "phone": None, 
                "website": None, 
                "rating": 4.4, 
                "reviews": 156, 
                "category": "Spa", 
                "address": "Patiala", 
                "lat": 30.33, 
                "lng": 76.39, 
                "maps_url": "https://maps.google.com/8",
                "source_job_id": "JOB-DEMO2",
                "status": "new"
            },
        ]
        
        # Add demo jobs first
        demo_jobs = [
            {
                "job_id": "JOB-DEMO1", 
                "keyword": "Dentist", 
                "location": "Ludhiana", 
                "radius": 10, 
                "grid_size": "10x10", 
                "status": "completed",
                "total_tasks": 100,
                "completed_tasks": 100,
                "leads_found": 4
            },
            {
                "job_id": "JOB-DEMO2", 
                "keyword": "Gym", 
                "location": "Punjab", 
                "radius": 25, 
                "grid_size": "15x15", 
                "status": "completed",
                "total_tasks": 225,
                "completed_tasks": 225,
                "leads_found": 4
            },
            {
                "job_id": "JOB-DEMO3", 
                "keyword": "Salon", 
                "location": "Delhi", 
                "radius": 15, 
                "grid_size": "10x10", 
                "status": "running",
                "total_tasks": 100,
                "completed_tasks": 45,
                "leads_found": 12
            },
        ]
        
        for job_data in demo_jobs:
            job = ScrapingJob(**job_data)
            db.add(job)
        db.commit()
        logger.info(f"Seeded {len(demo_jobs)} demo jobs")
        
        # Add businesses
        for biz_data in demo_businesses:
            biz = Business(**biz_data)
            db.add(biz)
        db.commit()
        logger.info(f"Seeded {len(demo_businesses)} demo businesses")
        
        # Add analysis data
        analyses = [
            {"business_id": 1, "lead_type": "NO_WEBSITE", "lead_score": 7, "ssl_enabled": False, "mobile_friendly": False, "load_time": 0},
            {"business_id": 2, "lead_type": "WEBSITE_REDESIGN", "lead_score": 5, "ssl_enabled": False, "mobile_friendly": False, "load_time": 3.2},
            {"business_id": 3, "lead_type": "NO_WEBSITE", "lead_score": 6, "ssl_enabled": False, "mobile_friendly": False, "load_time": 0},
            {"business_id": 4, "lead_type": "NORMAL", "lead_score": 3, "ssl_enabled": True, "mobile_friendly": True, "load_time": 1.5},
            {"business_id": 5, "lead_type": "WEBSITE_REDESIGN", "lead_score": 4, "ssl_enabled": False, "mobile_friendly": False, "load_time": 4.1},
            {"business_id": 6, "lead_type": "NO_WEBSITE", "lead_score": 8, "ssl_enabled": False, "mobile_friendly": False, "load_time": 0},
            {"business_id": 7, "lead_type": "WEBSITE_REDESIGN", "lead_score": 3, "ssl_enabled": False, "mobile_friendly": True, "load_time": 2.8},
            {"business_id": 8, "lead_type": "NO_WEBSITE", "lead_score": 5, "ssl_enabled": False, "mobile_friendly": False, "load_time": 0},
        ]
        
        for analysis_data in analyses:
            analysis = LeadAnalysis(**analysis_data)
            db.add(analysis)
        db.commit()
        logger.info(f"Seeded {len(analyses)} lead analyses")
        
        # Add sample blacklist entries
        blacklist_entries = [
            {"value": "+91 00000 00000", "type": "phone", "reason": "Spam number"},
            {"value": "test_place_id", "type": "place_id", "reason": "Test entry"},
        ]
        
        for bl_data in blacklist_entries:
            bl = Blacklist(**bl_data)
            db.add(bl)
        db.commit()
        logger.info(f"Seeded {len(blacklist_entries)} blacklist entries")
        
        logger.info("Demo data seeded successfully!")
        return {"message": "Demo data seeded successfully", "businesses": len(demo_businesses)}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


def clear_all_data():
    """Clear all data from the database (use with caution!)."""
    db = SessionLocal()
    try:
        db.query(LeadAnalysis).delete()
        db.query(Business).delete()
        db.query(ScrapingJob).delete()
        db.query(Blacklist).delete()
        db.commit()
        logger.info("All data cleared")
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        clear_all_data()
    else:
        seed_demo_data()
