"""
Database models for Zillow property listings
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import re

Base = declarative_base()

class Property(Base):
    """Property listing model"""
    __tablename__ = 'properties'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Search term to differentiate different house searches
    search_term = Column(String(255), nullable=False, index=True)
    
    # Basic property information
    address = Column(String(500), nullable=False)
    price = Column(String(100))
    sold_by = Column(String(100))
    url = Column(Text)
    
    # Coordinates from search config
    ne_lat = Column(Float)
    ne_long = Column(Float)
    sw_lat = Column(Float)
    sw_long = Column(Float)
    
    # Attribution information (stored as JSON for flexibility)
    attribution_agent_email = Column(String(255))
    attribution_agent_license_number = Column(String(100))
    attribution_agent_name = Column(String(255))
    attribution_agent_phone_number = Column(String(50))
    attribution_title = Column(String(255))
    attribution_broker_name = Column(String(255))
    attribution_broker_phone_number = Column(String(50))
    attribution_buyer_agent_member_state_license = Column(String(100))
    attribution_buyer_agent_name = Column(String(255))
    attribution_buyer_brokerage_name = Column(String(255))
    attribution_co_agent_license_number = Column(String(100))
    attribution_co_agent_name = Column(String(255))
    attribution_co_agent_number = Column(String(50))
    attribution_last_checked = Column(String(100))
    attribution_last_updated = Column(String(100))
    attribution_listing_offices = Column(Text)  # Store as JSON string
    attribution_listing_agents = Column(Text)  # Store as JSON string
    attribution_mls_disclaimer = Column(Text)
    attribution_mls_id = Column(String(100))
    attribution_mls_name = Column(String(255))
    attribution_provider_logo = Column(Text)
    attribution_listing_agreement = Column(String(255))
    attribution_listing_attribution_contact = Column(String(255))
    attribution_listing_agent_attribution_contact = Column(String(255))
    attribution_info_string3 = Column(Text)
    attribution_info_string5 = Column(Text)
    attribution_info_string10 = Column(Text)
    attribution_info_string16 = Column(Text)
    attribution_true_status = Column(String(100))
    
    # Additional attribution data (catch-all for any extra fields)
    attribution_extra = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Property(id={self.id}, address='{self.address}', search_term='{self.search_term}')>"


class SearchConfig(Base):
    """Search configuration model"""
    __tablename__ = 'search_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Search configuration parameters
    search_value = Column(String(500), nullable=False, unique=True)
    ne_lat = Column(Float, nullable=False)
    ne_long = Column(Float, nullable=False)
    sw_lat = Column(Float, nullable=False)
    sw_long = Column(Float, nullable=False)
    pagination = Column(Integer, default=1)
    
    # Additional metadata
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SearchConfig(id={self.id}, search_value='{self.search_value}')>"


class MessageTemplate(Base):
    """Message template model"""
    __tablename__ = 'message_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Template information
    name = Column(String(255), nullable=False, unique=True)
    template_text = Column(Text, nullable=False)
    is_default = Column(Integer, default=0)  # 1 for default, 0 for regular
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    
    # Template metadata
    description = Column(Text)
    category = Column(String(100), default='general')  # e.g., 'initial', 'follow_up', 'custom'
    
    # Available variables for this template
    available_variables = Column(Text)  # JSON string of available variables
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<MessageTemplate(id={self.id}, name='{self.name}', is_default={self.is_default})>"


class ScraperConfig(Base):
    """Scraper configuration model"""
    __tablename__ = 'scraper_configs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Scheduling configuration
    is_enabled = Column(Integer, default=1)  # 1 for enabled, 0 for disabled
    schedule_interval_minutes = Column(Integer, default=10)  # Run every X minutes
    last_scheduled_run = Column(DateTime)
    next_scheduled_run = Column(DateTime)
    
    # Scraper settings
    max_concurrent_workers = Column(Integer, default=5)
    timeout_minutes = Column(Integer, default=5)
    retry_attempts = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScraperConfig(id={self.id}, enabled={self.is_enabled}, interval={self.schedule_interval_minutes}min)>"


class ScraperLog(Base):
    """Scraper execution log model"""
    __tablename__ = 'scraper_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Execution details
    execution_id = Column(String(50), nullable=False, index=True)  # Unique ID for each run
    status = Column(String(50), nullable=False)  # 'running', 'completed', 'failed', 'cancelled'
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    
    # Results
    total_searches = Column(Integer, default=0)
    successful_searches = Column(Integer, default=0)
    total_properties = Column(Integer, default=0)
    properties_saved = Column(Integer, default=0)
    
    # Error information
    error_message = Column(Text)
    error_details = Column(Text)
    
    # Log file path
    log_file_path = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScraperLog(id={self.id}, execution_id='{self.execution_id}', status='{self.status}')>"


class DatabaseManager:
    """Database manager for handling database operations"""
    
    def __init__(self, database_url='sqlite:///zillow_properties.db'):
        """
        Initialize database connection
        
        Args:
            database_url: Database connection string (defaults to SQLite)
        """
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_property(self, property_data, search_config):
        """
        Add a property to the database
        
        Args:
            property_data: Dictionary containing property information
            search_config: Dictionary containing search configuration
        """
        # Prepare attribution fields
        attribution_fields = {}
        extra_attribution = {}
        
        # Debug: Print what we're receiving
        print(f"    Processing property: {property_data.get('Address', 'Unknown')}")
        
        # Map the attribution fields from the property_data
        for key, value in property_data.items():
            if key.startswith('Attribution_'):
                # Remove 'Attribution_' prefix 
                field_name = key.replace('Attribution_', '')
                
                # Convert field name to match database column naming
                # Handle specific mappings
                field_mapping = {
                    'agentEmail': 'agent_email',
                    'agentLicenseNumber': 'agent_license_number',
                    'agentName': 'agent_name',
                    'agentPhoneNumber': 'agent_phone_number',
                    'attributionTitle': 'title',
                    'brokerName': 'broker_name',
                    'brokerPhoneNumber': 'broker_phone_number',
                    'buyerAgentMemberStateLicense': 'buyer_agent_member_state_license',
                    'buyerAgentName': 'buyer_agent_name',
                    'buyerBrokerageName': 'buyer_brokerage_name',
                    'coAgentLicenseNumber': 'co_agent_license_number',
                    'coAgentName': 'co_agent_name',
                    'coAgentNumber': 'co_agent_number',
                    'lastChecked': 'last_checked',
                    'lastUpdated': 'last_updated',
                    'listingOffices': 'listing_offices',
                    'listingAgents': 'listing_agents',
                    'mlsDisclaimer': 'mls_disclaimer',
                    'mlsId': 'mls_id',
                    'mlsName': 'mls_name',
                    'providerLogo': 'provider_logo',
                    'listingAgreement': 'listing_agreement',
                    'listingAttributionContact': 'listing_attribution_contact',
                    'listingAgentAttributionContact': 'listing_agent_attribution_contact',
                    'infoString3': 'info_string3',
                    'infoString5': 'info_string5',
                    'infoString10': 'info_string10',
                    'infoString16': 'info_string16',
                    'trueStatus': 'true_status'
                }
                
                # Get the mapped field name or convert to snake_case
                if field_name in field_mapping:
                    db_field_name = f'attribution_{field_mapping[field_name]}'
                else:
                    # Convert camelCase to snake_case for any unmapped fields
                    snake_case = re.sub('([A-Z]+)', r'_\1', field_name).lower()
                    if snake_case.startswith('_'):
                        snake_case = snake_case[1:]
                    db_field_name = f'attribution_{snake_case}'
                
                # Check if this field exists in our model
                if hasattr(Property, db_field_name):
                    # Convert lists/dicts to JSON strings for storage
                    if isinstance(value, (list, dict)):
                        attribution_fields[db_field_name] = json.dumps(value)
                    else:
                        attribution_fields[db_field_name] = str(value) if value is not None else None
                else:
                    # Store in extra attribution field
                    extra_attribution[field_name] = value
        
        # Create property instance
        property_obj = Property(
            search_term=search_config['search_value'],
            address=property_data.get('Address', ''),
            price=property_data.get('Price', ''),
            sold_by=property_data.get('Sold_By', ''),
            url=property_data.get('Url', ''),
            ne_lat=search_config.get('ne_lat'),
            ne_long=search_config.get('ne_long'),
            sw_lat=search_config.get('sw_lat'),
            sw_long=search_config.get('sw_long'),
            attribution_extra=extra_attribution if extra_attribution else None,
            **attribution_fields
        )
        
        self.session.add(property_obj)
        return property_obj
    
    def commit(self):
        """Commit the current transaction"""
        self.session.commit()
    
    def rollback(self):
        """Rollback the current transaction"""
        self.session.rollback()
    
    def close(self):
        """Close the database session"""
        self.session.close()
    
    def get_properties_by_search_term(self, search_term):
        """
        Get all properties for a specific search term
        
        Args:
            search_term: The search term to filter by
        
        Returns:
            List of Property objects
        """
        return self.session.query(Property).filter_by(search_term=search_term).all()
    
    def get_all_properties(self):
        """
        Get all properties from the database
        
        Returns:
            List of Property objects
        """
        return self.session.query(Property).all()
    
    def get_unique_search_terms(self):
        """
        Get all unique search terms
        
        Returns:
            List of unique search terms
        """
        result = self.session.query(Property.search_term).distinct().all()
        return [r[0] for r in result]
    
    def delete_properties_by_search_term(self, search_term):
        """
        Delete all properties for a specific search term
        
        Args:
            search_term: The search term to filter by
        """
        self.session.query(Property).filter_by(search_term=search_term).delete()
        self.commit()
    
    # Search Configuration Methods
    def add_search_config(self, config_data):
        """
        Add a new search configuration to the database
        
        Args:
            config_data: Dictionary containing search configuration
        
        Returns:
            SearchConfig object
        """
        search_config = SearchConfig(
            search_value=config_data['search_value'],
            ne_lat=config_data['ne_lat'],
            ne_long=config_data['ne_long'],
            sw_lat=config_data['sw_lat'],
            sw_long=config_data['sw_long'],
            pagination=config_data.get('pagination', 1),
            description=config_data.get('description', '')
        )
        
        self.session.add(search_config)
        return search_config
    
    def get_all_search_configs(self, active_only=True):
        """
        Get all search configurations from the database
        
        Args:
            active_only: If True, only return active configurations
        
        Returns:
            List of SearchConfig objects
        """
        query = self.session.query(SearchConfig)
        if active_only:
            query = query.filter_by(is_active=1)
        return query.all()
    
    def get_search_config_by_value(self, search_value):
        """
        Get a search configuration by search value
        
        Args:
            search_value: The search value to look for
        
        Returns:
            SearchConfig object or None
        """
        return self.session.query(SearchConfig).filter_by(search_value=search_value).first()
    
    def update_search_config(self, search_value, updates):
        """
        Update a search configuration
        
        Args:
            search_value: The search value to update
            updates: Dictionary containing fields to update
        
        Returns:
            True if updated, False if not found
        """
        config = self.get_search_config_by_value(search_value)
        if config:
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            config.updated_at = datetime.utcnow()
            self.commit()
            return True
        return False
    
    def delete_search_config(self, search_value):
        """
        Delete a search configuration
        
        Args:
            search_value: The search value to delete
        
        Returns:
            True if deleted, False if not found
        """
        config = self.get_search_config_by_value(search_value)
        if config:
            self.session.delete(config)
            self.commit()
            return True
        return False
    
    def deactivate_search_config(self, search_value):
        """
        Deactivate a search configuration (soft delete)
        
        Args:
            search_value: The search value to deactivate
        
        Returns:
            True if deactivated, False if not found
        """
        return self.update_search_config(search_value, {'is_active': 0})
    
    def activate_search_config(self, search_value):
        """
        Activate a search configuration
        
        Args:
            search_value: The search value to activate
        
        Returns:
            True if activated, False if not found
        """
        return self.update_search_config(search_value, {'is_active': 1})
    
    # Message Template Methods
    def add_message_template(self, template_data):
        """
        Add a new message template to the database
        
        Args:
            template_data: Dictionary containing template information
        
        Returns:
            MessageTemplate object
        """
        # If this is set as default, unset any existing default
        if template_data.get('is_default', False):
            self.clear_default_template()
        
        message_template = MessageTemplate(
            name=template_data['name'],
            template_text=template_data['template_text'],
            is_default=template_data.get('is_default', False),
            is_active=template_data.get('is_active', True),
            description=template_data.get('description', ''),
            category=template_data.get('category', 'general'),
            available_variables=template_data.get('available_variables', '')
        )
        
        self.session.add(message_template)
        return message_template
    
    def get_all_message_templates(self, active_only=True):
        """
        Get all message templates from the database
        
        Args:
            active_only: If True, only return active templates
        
        Returns:
            List of MessageTemplate objects
        """
        query = self.session.query(MessageTemplate)
        if active_only:
            query = query.filter_by(is_active=1)
        return query.order_by(MessageTemplate.is_default.desc(), MessageTemplate.name).all()
    
    def get_message_template_by_name(self, name):
        """
        Get a message template by name
        
        Args:
            name: The template name to look for
        
        Returns:
            MessageTemplate object or None
        """
        return self.session.query(MessageTemplate).filter_by(name=name).first()
    
    def get_default_message_template(self):
        """
        Get the default message template
        
        Returns:
            MessageTemplate object or None
        """
        return self.session.query(MessageTemplate).filter_by(is_default=1, is_active=1).first()
    
    def set_default_message_template(self, template_name):
        """
        Set a message template as the default
        
        Args:
            template_name: The name of the template to set as default
        
        Returns:
            True if set, False if template not found
        """
        # First, clear any existing default
        self.clear_default_template()
        
        # Set the new default
        template = self.get_message_template_by_name(template_name)
        if template:
            template.is_default = 1
            self.commit()
            return True
        return False
    
    def clear_default_template(self):
        """Clear the default flag from all templates"""
        self.session.query(MessageTemplate).filter_by(is_default=1).update({'is_default': 0})
    
    def update_message_template(self, template_name, updates):
        """
        Update a message template
        
        Args:
            template_name: The template name to update
            updates: Dictionary containing fields to update
        
        Returns:
            True if updated, False if not found
        """
        template = self.get_message_template_by_name(template_name)
        if template:
            # If setting as default, clear any existing default
            if updates.get('is_default', False):
                self.clear_default_template()
            
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = datetime.utcnow()
            self.commit()
            return True
        return False
    
    def delete_message_template(self, template_name):
        """
        Delete a message template
        
        Args:
            template_name: The template name to delete
        
        Returns:
            True if deleted, False if not found
        """
        template = self.get_message_template_by_name(template_name)
        if template:
            # Don't allow deletion of default template
            if template.is_default:
                print(f"Cannot delete default template '{template_name}'. Set another template as default first.")
                return False
            
            self.session.delete(template)
            self.commit()
            return True
        return False
    
    def deactivate_message_template(self, template_name):
        """
        Deactivate a message template (soft delete)
        
        Args:
            template_name: The template name to deactivate
        
        Returns:
            True if deactivated, False if not found
        """
        return self.update_message_template(template_name, {'is_active': 0})
    
    def activate_message_template(self, template_name):
        """
        Activate a message template
        
        Args:
            template_name: The template name to activate
        
        Returns:
            True if activated, False if not found
        """
        return self.update_message_template(template_name, {'is_active': 1})
    
    def get_template_variables(self, template_name):
        """
        Get available variables for a template
        
        Args:
            template_name: The template name
        
        Returns:
            List of available variables or empty list
        """
        template = self.get_message_template_by_name(template_name)
        if template and template.available_variables:
            try:
                return json.loads(template.available_variables)
            except json.JSONDecodeError:
                return []
        return []

    # Scraper Configuration Methods
    def get_scraper_config(self):
        """
        Get the scraper configuration (creates default if none exists)
        
        Returns:
            ScraperConfig object
        """
        config = self.session.query(ScraperConfig).first()
        if not config:
            # Create default configuration
            config = ScraperConfig()
            self.session.add(config)
            self.commit()
        return config
    
    def update_scraper_config(self, updates):
        """
        Update scraper configuration
        
        Args:
            updates: Dictionary containing fields to update
        
        Returns:
            True if updated successfully
        """
        try:
            config = self.get_scraper_config()
            
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_at = datetime.utcnow()
            self.commit()
            return True
        except Exception as e:
            print(f"Error updating scraper config: {str(e)}")
            return False
    
    def schedule_next_run(self):
        """
        Calculate and set the next scheduled run time
        
        Returns:
            DateTime of next run
        """
        from datetime import timedelta
        config = self.get_scraper_config()
        if config.is_enabled:
            if config.next_scheduled_run is None:
                config.next_scheduled_run = datetime.utcnow()
            else:
                config.next_scheduled_run = datetime.utcnow() + timedelta(minutes=config.schedule_interval_minutes)
            config.last_scheduled_run = datetime.utcnow()
            self.commit()
            return config.next_scheduled_run
        return None
    
    # Scraper Logging Methods
    def create_scraper_log(self, execution_id):
        """
        Create a new scraper log entry
        
        Args:
            execution_id: Unique identifier for this execution
        
        Returns:
            ScraperLog object
        """
        log = ScraperLog(
            execution_id=execution_id,
            status='running',
            start_time=datetime.utcnow()
        )
        self.session.add(log)
        self.commit()
        return log
    
    def update_scraper_log(self, execution_id, updates):
        """
        Update a scraper log entry
        
        Args:
            execution_id: The execution ID to update
            updates: Dictionary containing fields to update
        
        Returns:
            True if updated successfully
        """
        try:
            log = self.session.query(ScraperLog).filter_by(execution_id=execution_id).first()
            if log:
                for key, value in updates.items():
                    if hasattr(log, key):
                        setattr(log, key, value)
                self.commit()
                return True
            return False
        except Exception as e:
            print(f"Error updating scraper log: {str(e)}")
            return False
    
    def get_scraper_logs(self, limit=50):
        """
        Get recent scraper logs
        
        Args:
            limit: Maximum number of logs to return
        
        Returns:
            List of ScraperLog objects
        """
        return self.session.query(ScraperLog).order_by(ScraperLog.created_at.desc()).limit(limit).all()
    
    def get_scraper_log_by_id(self, execution_id):
        """
        Get a specific scraper log by execution ID
        
        Args:
            execution_id: The execution ID to look for
        
        Returns:
            ScraperLog object or None
        """
        return self.session.query(ScraperLog).filter_by(execution_id=execution_id).first()
    
    def cleanup_old_logs(self, days_to_keep=30):
        """
        Clean up old scraper logs
        
        Args:
            days_to_keep: Number of days of logs to keep
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        self.session.query(ScraperLog).filter(ScraperLog.created_at < cutoff_date).delete()
        self.commit()
