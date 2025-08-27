"""
Scraper scheduler for Zillow Property Manager
"""
import threading
import time
import schedule
from datetime import datetime, timedelta
from database_models import DatabaseManager
from scraper_logger import ScraperLogger
import subprocess
import os

class ScraperScheduler:
    """Handles scheduling and running of scraper jobs"""
    
    def __init__(self):
        """Initialize the scheduler"""
        self.db_manager = DatabaseManager()
        self.scheduler_thread = None
        self.is_running = False
        self.current_job = None
        
        # Load initial configuration
        self.config = self.db_manager.get_scraper_config()
        self.db_manager.close()
        
        # Set up the scheduler
        self.setup_scheduler()
    
    def setup_scheduler(self):
        """Set up the scheduled job"""
        # Clear any existing jobs
        schedule.clear()
        
        if self.config.is_enabled:
            # Schedule the job to run every X minutes
            schedule.every(self.config.schedule_interval_minutes).minutes.do(self.run_scheduled_scraper)
            
            # If we have a next scheduled run time, calculate when to start
            if self.config.next_scheduled_run:
                time_until_next = (self.config.next_scheduled_run - datetime.utcnow()).total_seconds()
                if time_until_next > 0:
                    # Schedule the first run at the specific time
                    schedule.every().day.at(self.config.next_scheduled_run.strftime("%H:%M")).do(self.run_scheduled_scraper)
            
            print(f"Scraper scheduled to run every {self.config.schedule_interval_minutes} minutes")
        else:
            print("Scraper scheduling is disabled")
    
    def start(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            print("Scheduler is already running")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        print("Scraper scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("Scraper scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)  # Check every second
            except Exception as e:
                print(f"Error in scheduler: {str(e)}")
                time.sleep(5)  # Wait a bit longer on error
    
    def run_scheduled_scraper(self):
        """Run the scraper as a scheduled job"""
        try:
            print(f"Running scheduled scraper at {datetime.now()}")
            
            # Check if scraper is already running
            if self.current_job and self.current_job.is_alive():
                print("Scraper is already running, skipping scheduled run")
                return
            
            # Run scraper in background
            self.current_job = threading.Thread(target=self._run_scraper_process, daemon=True)
            self.current_job.start()
            
            # Schedule next run
            self.db_manager = DatabaseManager()
            next_run = self.db_manager.schedule_next_run()
            self.db_manager.close()
            
            if next_run:
                print(f"Next scheduled run: {next_run}")
            
        except Exception as e:
            print(f"Error running scheduled scraper: {str(e)}")
    
    def _run_scraper_process(self):
        """Run the scraper process"""
        try:
            # Run the scraper script
            result = subprocess.run(
                ['python', 'get_listing_and_agent.py'], 
                capture_output=True, 
                text=True, 
                timeout=self.config.timeout_minutes * 60
            )
            
            if result.returncode == 0:
                print("Scheduled scraper completed successfully")
            else:
                print(f"Scheduled scraper failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"Scheduled scraper timed out after {self.config.timeout_minutes} minutes")
        except Exception as e:
            print(f"Error running scheduled scraper: {str(e)}")
        finally:
            self.current_job = None
    
    def update_config(self, new_config):
        """
        Update the scheduler configuration
        
        Args:
            new_config: Dictionary containing new configuration values
        """
        try:
            self.db_manager = DatabaseManager()
            success = self.db_manager.update_scraper_config(new_config)
            self.db_manager.close()
            
            if success:
                # Reload configuration and restart scheduler
                self.db_manager = DatabaseManager()
                self.config = self.db_manager.get_scraper_config()
                self.db_manager.close()
                
                self.setup_scheduler()
                print("Scheduler configuration updated")
                return True
            else:
                print("Failed to update scheduler configuration")
                return False
                
        except Exception as e:
            print(f"Error updating scheduler configuration: {str(e)}")
            return False
    
    def get_status(self):
        """
        Get the current scheduler status
        
        Returns:
            Dictionary with scheduler status information
        """
        try:
            self.db_manager = DatabaseManager()
            config = self.db_manager.get_scraper_config()
            
            status = {
                'is_enabled': bool(config.is_enabled),
                'schedule_interval_minutes': config.schedule_interval_minutes,
                'last_scheduled_run': config.last_scheduled_run.isoformat() if config.last_scheduled_run else None,
                'next_scheduled_run': config.next_scheduled_run.isoformat() if config.next_scheduled_run else None,
                'max_concurrent_workers': config.max_concurrent_workers,
                'timeout_minutes': config.timeout_minutes,
                'retry_attempts': config.retry_attempts,
                'scheduler_running': self.is_running,
                'current_job_running': self.current_job is not None and self.current_job.is_alive()
            }
            
            self.db_manager.close()
            return status
            
        except Exception as e:
            print(f"Error getting scheduler status: {str(e)}")
            return {
                'error': str(e),
                'is_enabled': False,
                'scheduler_running': False
            }
    
    def run_now(self):
        """Run the scraper immediately (manual trigger)"""
        if self.current_job and self.current_job.is_alive():
            return {'success': False, 'message': 'Scraper is already running'}
        
        try:
            self.current_job = threading.Thread(target=self._run_scraper_process, daemon=True)
            self.current_job.start()
            return {'success': True, 'message': 'Scraper started manually'}
        except Exception as e:
            return {'success': False, 'message': f'Error starting scraper: {str(e)}'}

# Global scheduler instance
scheduler = None

def get_scheduler():
    """Get the global scheduler instance"""
    global scheduler
    if scheduler is None:
        scheduler = ScraperScheduler()
    return scheduler

def start_scheduler():
    """Start the global scheduler"""
    get_scheduler().start()

def stop_scheduler():
    """Stop the global scheduler"""
    global scheduler
    if scheduler:
        scheduler.stop()
        scheduler = None
