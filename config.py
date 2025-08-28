"""
Configuration settings for the Zillow Property Manager application
"""
import os

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'zillow_property_manager_secret_key_2024'
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///zillow_properties.db'
    
    # Flask configuration
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Application settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))
    
    # File paths
    LOG_DIR = os.environ.get('LOG_DIR', 'logs')
    CSV_EXPORT_DIR = os.environ.get('CSV_EXPORT_DIR', 'csv_exports')
    STATIC_EXPORT_DIR = os.environ.get('STATIC_EXPORT_DIR', 'static/exports')
    STATIC_LOG_DIR = os.environ.get('STATIC_LOG_DIR', 'static/logs')
    
    # Twilio configuration
    TWILIO_CONFIG_FILE = os.environ.get('TWILIO_CONFIG_FILE', 'twilio_config.json')
    
    # Scraper configuration
    SCRAPER_SCHEDULE_FILE = os.environ.get('SCRAPER_SCHEDULE_FILE', 'scraper_schedule.json')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'

class DockerConfig(Config):
    """Docker-specific configuration"""
    # Use data directory for database in Docker
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///data/zillow_properties.db'
    
    # Ensure directories exist
    LOG_DIR = '/app/logs'
    CSV_EXPORT_DIR = '/app/csv_exports'
    STATIC_EXPORT_DIR = '/app/static/exports'
    STATIC_LOG_DIR = '/app/static/logs'

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': ProductionConfig
}
