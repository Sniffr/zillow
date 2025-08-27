"""
Test script to verify attribution data is being saved correctly in the database
"""
from database_models import DatabaseManager, Property
import json

def test_attribution_saving():
    """Test that attribution data is being saved correctly"""
    print("Testing Attribution Data Saving")
    print("="*60)
    
    # Initialize database
    db_manager = DatabaseManager()
    print("✓ Database connection established")
    
    # Test data with various attribution fields (mimicking real Zillow data)
    test_property = {
        'Address': '123 Test Street, Los Angeles, CA 90001',
        'Price': '$750,000',
        'Sold_By': 'For Sale by Agent',
        'Url': 'https://www.zillow.com/test',
        # Attribution fields as they come from Zillow
        'Attribution_agentEmail': 'test.agent@realty.com',
        'Attribution_agentLicenseNumber': 'DRE # 01234567',
        'Attribution_agentName': 'Jane Smith',
        'Attribution_agentPhoneNumber': '310-555-1234',
        'Attribution_brokerName': 'Premium Realty Group',
        'Attribution_brokerPhoneNumber': '310-555-5678',
        'Attribution_coAgentName': 'John Doe',
        'Attribution_coAgentNumber': '310-555-9012',
        'Attribution_coAgentLicenseNumber': 'DRE # 98765432',
        'Attribution_mlsId': 'MLS123456',
        'Attribution_mlsName': 'California Regional MLS',
        'Attribution_lastChecked': '2025-01-01 10:00:00',
        'Attribution_lastUpdated': '2024-12-31 15:30:00',
        'Attribution_listingOffices': json.dumps([
            {'associatedOfficeType': 'listOffice', 'officeName': 'Premium Realty Group'}
        ]),
        'Attribution_listingAgents': json.dumps([
            {'associatedAgentType': 'listAgent', 'memberFullName': 'Jane Smith', 'memberStateLicense': 'DRE # 01234567'}
        ])
    }
    
    test_config = {
        'search_value': 'Test Properties in Los Angeles',
        'ne_lat': 34.05,
        'ne_long': -118.24,
        'sw_lat': 33.70,
        'sw_long': -118.67
    }
    
    # Clean up any existing test data first
    existing = db_manager.get_properties_by_search_term(test_config['search_value'])
    if existing:
        print(f"Cleaning up {len(existing)} existing test properties...")
        db_manager.delete_properties_by_search_term(test_config['search_value'])
    
    # Add property with attribution data
    print("\nAdding property with attribution data...")
    try:
        prop = db_manager.add_property(test_property, test_config)
        db_manager.commit()
        print(f"✓ Added test property with ID: {prop.id}")
    except Exception as e:
        print(f"✗ Error adding property: {e}")
        db_manager.rollback()
        db_manager.close()
        return False
    
    # Retrieve and verify the property
    print("\nVerifying saved attribution data...")
    properties = db_manager.get_properties_by_search_term(test_config['search_value'])
    
    if not properties:
        print("✗ Failed to retrieve property")
        db_manager.close()
        return False
    
    prop = properties[0]
    print(f"✓ Retrieved property: {prop.address}")
    
    # Check all attribution fields
    attribution_checks = [
        ('agent_email', 'test.agent@realty.com'),
        ('agent_name', 'Jane Smith'),
        ('agent_phone_number', '310-555-1234'),
        ('agent_license_number', 'DRE # 01234567'),
        ('broker_name', 'Premium Realty Group'),
        ('broker_phone_number', '310-555-5678'),
        ('co_agent_name', 'John Doe'),
        ('co_agent_number', '310-555-9012'),
        ('co_agent_license_number', 'DRE # 98765432'),
        ('mls_id', 'MLS123456'),
        ('mls_name', 'California Regional MLS'),
    ]
    
    all_passed = True
    print("\nAttribution Field Verification:")
    print("-" * 40)
    
    for field_name, expected_value in attribution_checks:
        db_field = f'attribution_{field_name}'
        actual_value = getattr(prop, db_field, None)
        
        if actual_value == expected_value:
            print(f"  ✓ {field_name}: {actual_value}")
        else:
            print(f"  ✗ {field_name}: Expected '{expected_value}', Got '{actual_value}'")
            all_passed = False
    
    # Check JSON fields
    print("\nJSON Field Verification:")
    print("-" * 40)
    
    if prop.attribution_listing_offices:
        try:
            offices = json.loads(prop.attribution_listing_offices)
            print(f"  ✓ listing_offices: {len(offices)} office(s) stored")
        except:
            print(f"  ✗ listing_offices: Failed to parse JSON")
            all_passed = False
    
    if prop.attribution_listing_agents:
        try:
            agents = json.loads(prop.attribution_listing_agents)
            print(f"  ✓ listing_agents: {len(agents)} agent(s) stored")
        except:
            print(f"  ✗ listing_agents: Failed to parse JSON")
            all_passed = False
    
    # Test phone number extraction for messaging
    print("\nPhone Number Extraction Test:")
    print("-" * 40)
    
    phone_fields = [
        ('Agent Phone', prop.attribution_agent_phone_number),
        ('Broker Phone', prop.attribution_broker_phone_number),
        ('Co-Agent Phone', prop.attribution_co_agent_number)
    ]
    
    for label, phone in phone_fields:
        if phone:
            print(f"  ✓ {label}: {phone}")
        else:
            print(f"  ✗ {label}: Not found")
    
    # Clean up test data
    print("\nCleaning up test data...")
    db_manager.delete_properties_by_search_term(test_config['search_value'])
    print("✓ Test data cleaned up")
    
    # Close connection
    db_manager.close()
    print("✓ Database connection closed")
    
    # Final result
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL ATTRIBUTION TESTS PASSED!")
        print("Attribution data is being saved correctly to the database.")
    else:
        print("⚠️  SOME ATTRIBUTION TESTS FAILED")
        print("Please check the field mappings in database_models.py")
    print("="*60)
    
    return all_passed

def display_sample_data():
    """Display sample data from the database to verify attribution fields"""
    print("\n" + "="*60)
    print("DISPLAYING SAMPLE DATA FROM DATABASE")
    print("="*60)
    
    db_manager = DatabaseManager()
    
    # Get all properties
    properties = db_manager.get_all_properties()
    
    if not properties:
        print("No properties found in database.")
        db_manager.close()
        return
    
    # Show first property with full attribution details
    prop = properties[0]
    print(f"\nSample Property Details:")
    print("-" * 40)
    print(f"ID: {prop.id}")
    print(f"Search Term: {prop.search_term}")
    print(f"Address: {prop.address}")
    print(f"Price: {prop.price}")
    print(f"URL: {prop.url}")
    
    print(f"\nAttribution Details:")
    print("-" * 40)
    
    # Display all attribution fields
    for column in Property.__table__.columns:
        if column.name.startswith('attribution_'):
            value = getattr(prop, column.name)
            if value:
                display_name = column.name.replace('attribution_', '').replace('_', ' ').title()
                # Truncate long values for display
                if isinstance(value, str) and len(value) > 100:
                    value = value[:97] + "..."
                print(f"{display_name}: {value}")
    
    # Count properties with phone numbers
    properties_with_phones = 0
    unique_phones = set()
    
    for prop in properties:
        has_phone = False
        if prop.attribution_agent_phone_number:
            unique_phones.add(prop.attribution_agent_phone_number)
            has_phone = True
        if prop.attribution_broker_phone_number:
            unique_phones.add(prop.attribution_broker_phone_number)
            has_phone = True
        if prop.attribution_co_agent_number:
            unique_phones.add(prop.attribution_co_agent_number)
            has_phone = True
        if has_phone:
            properties_with_phones += 1
    
    print(f"\nDatabase Statistics:")
    print("-" * 40)
    print(f"Total Properties: {len(properties)}")
    print(f"Properties with Phone Numbers: {properties_with_phones}")
    print(f"Unique Phone Numbers: {len(unique_phones)}")
    
    db_manager.close()

if __name__ == "__main__":
    # Run attribution test
    test_result = test_attribution_saving()
    
    # Display sample data from actual database
    display_sample_data()
