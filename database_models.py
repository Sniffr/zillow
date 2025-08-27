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
