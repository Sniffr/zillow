"""
Migration script to add scraper configuration and logging tables
"""
from database_models import DatabaseManager, ScraperConfig, ScraperLog
from sqlalchemy import inspect

def migrate_scraper_tables():
    """Add scraper configuration and logging tables to the database"""
    print("Starting scraper tables migration...")
    
    try:
        db_manager = DatabaseManager()
        
        # Check if tables already exist
        inspector = inspect(db_manager.engine)
        existing_tables = inspector.get_table_names()
        
        if 'scraper_configs' in existing_tables and 'scraper_logs' in existing_tables:
            print("Scraper tables already exist. Skipping migration.")
            return True
        
        # Create tables
        print("Creating scraper tables...")
        ScraperConfig.__table__.create(db_manager.engine, checkfirst=True)
        ScraperLog.__table__.create(db_manager.engine, checkfirst=True)
        
        # Create default scraper configuration
        print("Creating default scraper configuration...")
        default_config = ScraperConfig(
            is_enabled=1,
            schedule_interval_minutes=10,
            max_concurrent_workers=5,
            timeout_minutes=5,
            retry_attempts=3
        )
        
        db_manager.session.add(default_config)
        db_manager.commit()
        
        print("Migration completed successfully!")
        print("✓ scraper_configs table created")
        print("✓ scraper_logs table created")
        print("✓ Default configuration added")
        
        db_manager.close()
        return True
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        if 'db_manager' in locals():
            db_manager.close()
        return False

if __name__ == "__main__":
    success = migrate_scraper_tables()
    if success:
        print("\n🎉 Scraper tables migration completed successfully!")
    else:
        print("\n❌ Scraper tables migration failed!")
        exit(1)
