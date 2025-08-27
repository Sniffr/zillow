import pyzill
import json
import pandas as pd
import os
from database_models import DatabaseManager, Property
from sqlalchemy.exc import SQLAlchemyError

import send_agent_messages


# Read configurations from the JSON file
def load_search_configs(config_file):
    """Load search configurations from a JSON file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{config_file}'.")
        return []

def process_search_config(config, proxy_url):
    """Process a single search configuration"""
    print(f"Processing search: {config['search_value']}")
    
    results_sale = pyzill.for_sale(
        config['pagination'],
        search_value=config['search_value'],
        min_beds=None, max_beds=None,
        min_bathrooms=None, max_bathrooms=None,
        min_price=None, max_price=None,
        ne_lat=config['ne_lat'], 
        ne_long=config['ne_long'], 
        sw_lat=config['sw_lat'], 
        sw_long=config['sw_long'],
        zoom_value=10,
        proxy_url=proxy_url
    )
    
    # Get the map results
    map_result = results_sale['mapResults']
    
    # Create a list to store all property data for this search
    properties_data = []
    
    # Process properties (limit to 10 for testing, remove limit for production)
    for i in range(min(10, len(map_result))):
        property_url = "https://www.zillow.com" + map_result[i]['detailUrl']
        data = pyzill.get_from_home_url(property_url, proxy_url)
        
        # Create a dictionary for this property
        property_dict = {
            'Address': map_result[i]['address'],
            'Price': map_result[i]['price'],
            'Sold_By': map_result[i]['marketingStatusSimplifiedCd'],
            'Url': property_url
        }
        
        # Flatten attribution data into individual columns
        if 'attributionInfo' in data and data['attributionInfo']:
            for key, value in data['attributionInfo'].items():
                # Clean the column name by removing special characters and spaces
                clean_key = key.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
                property_dict[f'Attribution_{clean_key}'] = value
        
        properties_data.append(property_dict)
    
    print(f"  Found {len(properties_data)} properties for '{config['search_value']}'")
    return properties_data

def save_search_to_database(properties_data, config, db_manager):
    """Save search results to the database"""
    if not properties_data:
        print(f"  No properties to save for '{config['search_value']}'")
        return 0
    
    saved_count = 0
    try:
        # First, optionally delete existing properties for this search term
        # This ensures we don't have duplicates when re-running searches
        existing_properties = db_manager.get_properties_by_search_term(config['search_value'])
        if existing_properties:
            print(f"  Found {len(existing_properties)} existing properties for '{config['search_value']}', removing old data...")
            db_manager.delete_properties_by_search_term(config['search_value'])
        
        # Add each property to the database
        for property_data in properties_data:
            db_manager.add_property(property_data, config)
            saved_count += 1
        
        # Commit all changes
        db_manager.commit()
        print(f"  Saved {saved_count} properties to database for '{config['search_value']}'")
        
    except SQLAlchemyError as e:
        print(f"  Database error while saving properties: {str(e)}")
        db_manager.rollback()
        return 0
    
    return saved_count

def export_database_to_csv(db_manager, output_dir='csv_exports'):
    """Export database contents to CSV files by search term"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    search_terms = db_manager.get_unique_search_terms()
    exported_files = []
    
    for search_term in search_terms:
        properties = db_manager.get_properties_by_search_term(search_term)
        if properties:
            # Convert properties to dictionary format
            data = []
            for prop in properties:
                prop_dict = {
                    'search_term': prop.search_term,
                    'address': prop.address,
                    'price': prop.price,
                    'sold_by': prop.sold_by,
                    'url': prop.url,
                    'created_at': prop.created_at,
                    'updated_at': prop.updated_at
                }
                # Add attribution fields
                for col in Property.__table__.columns:
                    if col.name.startswith('attribution_') and col.name != 'attribution_extra':
                        value = getattr(prop, col.name)
                        if value:
                            prop_dict[col.name] = value
                data.append(prop_dict)
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(data)
            clean_search_name = search_term.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '').replace(',', '')
            filename = f"{clean_search_name}.csv"
            filepath = os.path.join(output_dir, filename)
            df.to_csv(filepath, index=False)
            exported_files.append(filepath)
            print(f"  Exported {len(properties)} properties to {filepath}")
    
    return exported_files

def main():
    # Configuration file path
    config_file = 'search_configs.json'
    
    # Load search configurations
    search_configs = load_search_configs(config_file)
    
    if not search_configs:
        print("No search configurations found. Please check your JSON file.")
        return
    
    # Initialize database manager
    db_manager = DatabaseManager()
    print("\nDatabase connection established.")
    print("Data will be stored in: zillow_properties.db")
    
    # Proxy configuration
    proxy_url = pyzill.parse_proxy("76cc06db4f59a17e.shg.na.pyproxy.io", "16666",
                                   "ASDAr32-zone-resi-region-us-session-78303445cfe9", "Fzsdf23")
    
    # Process each search configuration separately
    successful_searches = []
    total_properties_saved = 0
    
    for i, config in enumerate(search_configs):
        print(f"\nProcessing search {i+1}/{len(search_configs)}")
        try:
            properties_data = process_search_config(config, proxy_url)
            saved_count = save_search_to_database(properties_data, config, db_manager)
            if saved_count > 0:
                successful_searches.append(config['search_value'])
                total_properties_saved += saved_count
        except Exception as e:
            print(f"  Error processing search '{config['search_value']}': {str(e)}")
            continue
    
    # Summary
    print(f"\n{'='*50}")
    print("DATABASE STORAGE SUMMARY")
    print(f"{'='*50}")
    print(f"Total searches processed: {len(search_configs)}")
    print(f"Successful searches: {len(successful_searches)}")
    print(f"Total properties saved: {total_properties_saved}")
    
    if successful_searches:
        print(f"\nSearch terms stored in database:")
        for search_term in successful_searches:
            count = len(db_manager.get_properties_by_search_term(search_term))
            print(f"  ✓ {search_term}: {count} properties")
        
        # Show database statistics
        print(f"\nDatabase Statistics:")
        all_properties = db_manager.get_all_properties()
        unique_search_terms = db_manager.get_unique_search_terms()
        print(f"  Total properties in database: {len(all_properties)}")
        print(f"  Unique search terms: {len(unique_search_terms)}")
        
        # Optional: Export to CSV for backup/viewing
        export_choice = input("\nWould you like to export the database to CSV files? (y/n): ").lower()
        if export_choice == 'y':
            print("\nExporting database to CSV files...")
            exported_files = export_database_to_csv(db_manager)
            if exported_files:
                print(f"\nExported {len(exported_files)} CSV files:")
                for filepath in exported_files:
                    print(f"  ✓ {filepath}")
    else:
        print("No data was saved to the database.")
    
    # Close database connection
    db_manager.close()
    print("\nDatabase connection closed.")
    
    send_agent_messages.main()









if __name__ == "__main__":
    main()
