"""
Test script to verify database functionality
"""
from database_models import DatabaseManager, Property

def test_database():
    """Test basic database operations"""
    print("Testing Database Functionality")
    print("="*50)
    
    # Initialize database
    db_manager = DatabaseManager()
    print("✓ Database connection established")
    
    # Test data
    test_property = {
        'Address': '123 Test Street, Los Angeles, CA 90001',
        'Price': '$500,000',
        'Sold_By': 'For Sale by Agent',
        'Url': 'https://www.zillow.com/test',
        'Attribution_agentName': 'John Doe',
        'Attribution_agentEmail': 'john@example.com',
        'Attribution_brokerName': 'Test Realty'
    }
    
    test_config = {
        'search_value': 'Test Search Term',
        'ne_lat': 34.05,
        'ne_long': -118.24,
        'sw_lat': 33.70,
        'sw_long': -118.67
    }
    
    # Add property
    try:
        prop = db_manager.add_property(test_property, test_config)
        db_manager.commit()
        print(f"✓ Added test property: {prop}")
    except Exception as e:
        print(f"✗ Error adding property: {e}")
        db_manager.rollback()
        return
    
    # Retrieve property
    properties = db_manager.get_properties_by_search_term('Test Search Term')
    if properties:
        print(f"✓ Retrieved {len(properties)} properties for 'Test Search Term'")
        prop = properties[0]
        print(f"  - Address: {prop.address}")
        print(f"  - Price: {prop.price}")
        print(f"  - Search Term: {prop.search_term}")
    else:
        print("✗ Failed to retrieve properties")
    
    # Get unique search terms
    search_terms = db_manager.get_unique_search_terms()
    print(f"✓ Found {len(search_terms)} unique search terms: {search_terms}")
    
    # Clean up test data
    db_manager.delete_properties_by_search_term('Test Search Term')
    print("✓ Cleaned up test data")
    
    # Close connection
    db_manager.close()
    print("✓ Database connection closed")
    
    print("\n" + "="*50)
    print("All database tests passed successfully!")
    print("="*50)

if __name__ == "__main__":
    test_database()
