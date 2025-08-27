"""
Test script for the scraper logging and scheduling system
"""
import time
from datetime import datetime
from scraper_logger import ScraperLogger
from scraper_scheduler import ScraperScheduler
from database_models import DatabaseManager

def test_logging():
    """Test the scraper logging system"""
    print("Testing scraper logging system...")
    
    try:
        # Test logger creation
        with ScraperLogger() as logger:
            logger.info("This is a test log message")
            logger.warning("This is a test warning")
            logger.error("This is a test error")
            
            # Test progress updates
            logger.update_progress(5, 2, 100, 50)
            
            # Test completion
            logger.complete_success(5, 3, 100, 75)
            
        print("✓ Logging system test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Logging system test failed: {str(e)}")
        return False

def test_scheduler():
    """Test the scraper scheduler system"""
    print("\nTesting scraper scheduler system...")
    
    try:
        # Create scheduler
        scheduler = ScraperScheduler()
        
        # Test status
        status = scheduler.get_status()
        print(f"Scheduler status: {status}")
        
        # Test configuration update
        success = scheduler.update_config({
            'schedule_interval_minutes': 15,
            'timeout_minutes': 10
        })
        
        if success:
            print("✓ Configuration update test passed")
        else:
            print("✗ Configuration update test failed")
            return False
        
        # Test manual run
        result = scheduler.run_now()
        print(f"Manual run test: {result}")
        
        # Clean up
        scheduler.stop()
        
        print("✓ Scheduler system test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Scheduler system test failed: {str(e)}")
        return False

def test_database():
    """Test the database models"""
    print("\nTesting database models...")
    
    try:
        db_manager = DatabaseManager()
        
        # Test scraper config
        config = db_manager.get_scraper_config()
        print(f"Scraper config: {config}")
        
        # Test logs
        logs = db_manager.get_scraper_logs(limit=5)
        print(f"Found {len(logs)} log entries")
        
        db_manager.close()
        
        print("✓ Database models test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Database models test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Scraper Logging and Scheduling System")
    print("=" * 50)
    
    tests = [
        ("Database Models", test_database),
        ("Logging System", test_logging),
        ("Scheduler System", test_scheduler)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test PASSED")
        else:
            print(f"❌ {test_name} test FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
