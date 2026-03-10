"""
Database migration script for Lead Engine
Run this after deploying new code to add missing columns.
"""

import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///leadengine.db")

def run_migrations():
    engine = create_engine(DATABASE_URL)
    
    migrations = [
        # Add job progress tracking columns (March 2026)
        ("scraping_jobs", "total_tasks", "ALTER TABLE scraping_jobs ADD COLUMN total_tasks INTEGER DEFAULT 0"),
        ("scraping_jobs", "completed_tasks", "ALTER TABLE scraping_jobs ADD COLUMN completed_tasks INTEGER DEFAULT 0"),
        ("scraping_jobs", "leads_found", "ALTER TABLE scraping_jobs ADD COLUMN leads_found INTEGER DEFAULT 0"),
    ]
    
    with engine.connect() as conn:
        for table, column, sql in migrations:
            try:
                # Check if column exists (PostgreSQL)
                if "postgresql" in DATABASE_URL:
                    result = conn.execute(text(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = '{column}'
                    """))
                    if result.fetchone():
                        print(f"  [SKIP] Column {table}.{column} already exists")
                        continue
                
                # Run migration
                conn.execute(text(sql))
                conn.commit()
                print(f"  [OK] Added column {table}.{column}")
                
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"  [SKIP] Column {table}.{column} already exists")
                else:
                    print(f"  [ERROR] {table}.{column}: {e}")
    
    print("\nMigration complete!")

if __name__ == "__main__":
    print("Running database migrations...")
    run_migrations()
