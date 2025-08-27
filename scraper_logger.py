"""
Scraper logging utility for Zillow Property Manager
"""
import os
import logging
import uuid
from datetime import datetime
from database_models import DatabaseManager

class ScraperLogger:
    """Handles logging for scraper operations"""
    
    def __init__(self, execution_id=None):
        """
        Initialize the scraper logger
        
        Args:
            execution_id: Optional execution ID, will generate one if not provided
        """
        self.execution_id = execution_id or str(uuid.uuid4())
        self.db_manager = DatabaseManager()
        
        # Create logs directory if it doesn't exist
        self.logs_dir = os.path.join('static', 'logs')
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Set up file logging
        self.log_file_path = os.path.join(self.logs_dir, f'scraper_{self.execution_id}.log')
        
        # Configure logging
        self.logger = logging.getLogger(f'scraper_{self.execution_id}')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Create database log entry
        self.db_log = self.db_manager.create_scraper_log(self.execution_id)
        
        # Log start
        self.info(f"Scraper execution started with ID: {self.execution_id}")
    
    def info(self, message):
        """Log info message"""
        self.logger.info(message)
        print(f"[INFO] {message}")
    
    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
        print(f"[WARNING] {message}")
    
    def error(self, message):
        """Log error message"""
        self.logger.error(message)
        print(f"[ERROR] {message}")
    
    def debug(self, message):
        """Log debug message"""
        self.logger.debug(message)
        print(f"[DEBUG] {message}")
    
    def update_progress(self, total_searches, successful_searches, total_properties, properties_saved):
        """
        Update progress in database log
        
        Args:
            total_searches: Total number of searches to process
            successful_searches: Number of successful searches so far
            total_properties: Total properties found
            properties_saved: Number of properties saved to database
        """
        self.db_manager.update_scraper_log(self.execution_id, {
            'total_searches': total_searches,
            'successful_searches': successful_searches,
            'total_properties': total_properties,
            'properties_saved': properties_saved
        })
    
    def complete_success(self, total_searches, successful_searches, total_properties, properties_saved):
        """
        Mark scraper execution as successfully completed
        
        Args:
            total_searches: Total number of searches processed
            successful_searches: Number of successful searches
            total_properties: Total properties found
            properties_saved: Number of properties saved to database
        """
        self.info(f"Scraper completed successfully. "
                 f"Searches: {successful_searches}/{total_searches}, "
                 f"Properties: {properties_saved}/{total_properties}")
        
        self.db_manager.update_scraper_log(self.execution_id, {
            'status': 'completed',
            'end_time': datetime.utcnow(),
            'total_searches': total_searches,
            'successful_searches': successful_searches,
            'total_properties': total_properties,
            'properties_saved': properties_saved
        })
        
        self.close()
    
    def complete_failure(self, error_message, error_details=None):
        """
        Mark scraper execution as failed
        
        Args:
            error_message: Brief error message
            error_details: Detailed error information
        """
        self.error(f"Scraper failed: {error_message}")
        if error_details:
            self.error(f"Error details: {error_details}")
        
        self.db_manager.update_scraper_log(self.execution_id, {
            'status': 'failed',
            'end_time': datetime.utcnow(),
            'error_message': error_message,
            'error_details': error_details
        })
        
        self.close()
    
    def cancel(self):
        """Mark scraper execution as cancelled"""
        self.info("Scraper execution cancelled")
        
        self.db_manager.update_scraper_log(self.execution_id, {
            'status': 'cancelled',
            'end_time': datetime.utcnow()
        })
        
        self.close()
    
    def close(self):
        """Close the logger and clean up"""
        try:
            # Update log file path in database
            self.db_manager.update_scraper_log(self.execution_id, {
                'log_file_path': self.log_file_path
            })
            
            # Close database connection
            self.db_manager.close()
            
            # Remove handlers to prevent memory leaks
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
                
        except Exception as e:
            print(f"Error closing logger: {str(e)}")
    
    def get_log_content(self, max_lines=100):
        """
        Get the content of the log file
        
        Args:
            max_lines: Maximum number of lines to return
        
        Returns:
            List of log lines
        """
        try:
            if os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'r') as f:
                    lines = f.readlines()
                    return lines[-max_lines:] if len(lines) > max_lines else lines
            return []
        except Exception as e:
            return [f"Error reading log file: {str(e)}"]
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type is not None:
            self.complete_failure(str(exc_val))
        else:
            self.close()
