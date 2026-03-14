"""
Database migration script for Lead Engine.
Run this after deploying new code to add missing columns/tables.

Usage:
    python migrate.py          # Run all pending migrations
    python migrate.py --check  # Check migration status only
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///leadengine.db")


def get_existing_columns(engine, table_name):
    """Get list of existing columns in a table."""
    inspector = inspect(engine)
    try:
        columns = inspector.get_columns(table_name)
        return [col['name'] for col in columns]
    except:
        return []


def table_exists(engine, table_name):
    """Check if a table exists."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def run_migrations():
    """Run all pending database migrations."""
    engine = create_engine(DATABASE_URL)
    is_postgres = "postgresql" in DATABASE_URL
    is_sqlite = "sqlite" in DATABASE_URL
    
    logger.info(f"Running migrations on {'PostgreSQL' if is_postgres else 'SQLite'}")
    
    # Column migrations: (table, column, sql_postgres, sql_sqlite)
    column_migrations = [
        # Job progress tracking (existing)
        ("scraping_jobs", "total_tasks", 
         "ALTER TABLE scraping_jobs ADD COLUMN total_tasks INTEGER DEFAULT 0",
         "ALTER TABLE scraping_jobs ADD COLUMN total_tasks INTEGER DEFAULT 0"),
        ("scraping_jobs", "completed_tasks", 
         "ALTER TABLE scraping_jobs ADD COLUMN completed_tasks INTEGER DEFAULT 0",
         "ALTER TABLE scraping_jobs ADD COLUMN completed_tasks INTEGER DEFAULT 0"),
        ("scraping_jobs", "leads_found", 
         "ALTER TABLE scraping_jobs ADD COLUMN leads_found INTEGER DEFAULT 0",
         "ALTER TABLE scraping_jobs ADD COLUMN leads_found INTEGER DEFAULT 0"),
        
        # New job columns
        ("scraping_jobs", "failed_tasks", 
         "ALTER TABLE scraping_jobs ADD COLUMN failed_tasks INTEGER DEFAULT 0",
         "ALTER TABLE scraping_jobs ADD COLUMN failed_tasks INTEGER DEFAULT 0"),
        ("scraping_jobs", "error_message", 
         "ALTER TABLE scraping_jobs ADD COLUMN error_message TEXT",
         "ALTER TABLE scraping_jobs ADD COLUMN error_message TEXT"),
        ("scraping_jobs", "updated_at", 
         "ALTER TABLE scraping_jobs ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
         "ALTER TABLE scraping_jobs ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"),
        
        # Business enhancements
        ("businesses", "source_job_id", 
         "ALTER TABLE businesses ADD COLUMN source_job_id VARCHAR REFERENCES scraping_jobs(job_id)",
         "ALTER TABLE businesses ADD COLUMN source_job_id VARCHAR"),
        ("businesses", "tags", 
         "ALTER TABLE businesses ADD COLUMN tags VARCHAR",
         "ALTER TABLE businesses ADD COLUMN tags VARCHAR"),
        ("businesses", "notes", 
         "ALTER TABLE businesses ADD COLUMN notes TEXT",
         "ALTER TABLE businesses ADD COLUMN notes TEXT"),
        ("businesses", "status", 
         "ALTER TABLE businesses ADD COLUMN status VARCHAR DEFAULT 'new'",
         "ALTER TABLE businesses ADD COLUMN status VARCHAR DEFAULT 'new'"),
        ("businesses", "is_blacklisted", 
         "ALTER TABLE businesses ADD COLUMN is_blacklisted BOOLEAN DEFAULT FALSE",
         "ALTER TABLE businesses ADD COLUMN is_blacklisted INTEGER DEFAULT 0"),
        ("businesses", "updated_at", 
         "ALTER TABLE businesses ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
         "ALTER TABLE businesses ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"),
        
        # Lead analysis enhancements
        ("lead_analysis", "analyzed_at", 
         "ALTER TABLE lead_analysis ADD COLUMN analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
         "ALTER TABLE lead_analysis ADD COLUMN analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ]
    
    # Table creation migrations
    table_migrations = [
        # Blacklist table
        ("blacklist", """
            CREATE TABLE IF NOT EXISTS blacklist (
                id SERIAL PRIMARY KEY,
                value VARCHAR UNIQUE NOT NULL,
                type VARCHAR NOT NULL,
                reason VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """, """
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                value VARCHAR UNIQUE NOT NULL,
                type VARCHAR NOT NULL,
                reason VARCHAR,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """),
        
        # Job logs table
        ("job_logs", """
            CREATE TABLE IF NOT EXISTS job_logs (
                id SERIAL PRIMARY KEY,
                job_id VARCHAR REFERENCES scraping_jobs(job_id) ON DELETE CASCADE,
                level VARCHAR NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """, """
            CREATE TABLE IF NOT EXISTS job_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id VARCHAR,
                level VARCHAR NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """),
    ]
    
    # Index migrations
    index_migrations = [
        ("ix_business_category", "CREATE INDEX IF NOT EXISTS ix_business_category ON businesses(category)"),
        ("ix_business_status", "CREATE INDEX IF NOT EXISTS ix_business_status ON businesses(status)"),
        ("ix_business_phone", "CREATE INDEX IF NOT EXISTS ix_business_phone ON businesses(phone)"),
        ("ix_business_blacklist", "CREATE INDEX IF NOT EXISTS ix_business_blacklist ON businesses(is_blacklisted)"),
        ("ix_lead_type", "CREATE INDEX IF NOT EXISTS ix_lead_type ON lead_analysis(lead_type)"),
        ("ix_lead_score", "CREATE INDEX IF NOT EXISTS ix_lead_score ON lead_analysis(lead_score)"),
        ("ix_job_status", "CREATE INDEX IF NOT EXISTS ix_job_status ON scraping_jobs(status)"),
        ("ix_job_keyword", "CREATE INDEX IF NOT EXISTS ix_job_keyword ON scraping_jobs(keyword)"),
        ("ix_blacklist_value", "CREATE INDEX IF NOT EXISTS ix_blacklist_value ON blacklist(value)"),
        ("ix_blacklist_type", "CREATE INDEX IF NOT EXISTS ix_blacklist_type ON blacklist(type)"),
        ("ix_job_logs_job", "CREATE INDEX IF NOT EXISTS ix_job_logs_job ON job_logs(job_id)"),
        ("ix_job_logs_level", "CREATE INDEX IF NOT EXISTS ix_job_logs_level ON job_logs(level)"),
    ]
    
    with engine.connect() as conn:
        # Run table creation migrations
        for table_name, sql_postgres, sql_sqlite in table_migrations:
            if not table_exists(engine, table_name):
                try:
                    sql = sql_postgres if is_postgres else sql_sqlite
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info(f"[OK] Created table: {table_name}")
                except Exception as e:
                    logger.error(f"[ERROR] Creating table {table_name}: {e}")
            else:
                logger.info(f"[SKIP] Table {table_name} already exists")
        
        # Run column migrations
        for table, column, sql_postgres, sql_sqlite in column_migrations:
            existing_cols = get_existing_columns(engine, table)
            
            if column in existing_cols:
                logger.info(f"[SKIP] Column {table}.{column} already exists")
                continue
            
            try:
                sql = sql_postgres if is_postgres else sql_sqlite
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"[OK] Added column {table}.{column}")
            except Exception as e:
                error_str = str(e).lower()
                if "duplicate column" in error_str or "already exists" in error_str:
                    logger.info(f"[SKIP] Column {table}.{column} already exists")
                else:
                    logger.error(f"[ERROR] {table}.{column}: {e}")
        
        # Run index migrations
        for index_name, sql in index_migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"[OK] Created index: {index_name}")
            except Exception as e:
                error_str = str(e).lower()
                if "already exists" in error_str:
                    logger.info(f"[SKIP] Index {index_name} already exists")
                else:
                    logger.warning(f"[WARN] Index {index_name}: {e}")
    
    logger.info("\nMigration complete!")


def check_status():
    """Check current migration status."""
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    print("\n=== Database Migration Status ===\n")
    
    tables = inspector.get_table_names()
    print(f"Tables ({len(tables)}):")
    for table in sorted(tables):
        columns = inspector.get_columns(table)
        print(f"  - {table}: {len(columns)} columns")
    
    print("\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_status()
    else:
        print("Running database migrations...")
        run_migrations()

