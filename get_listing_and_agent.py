import pyzill
import json
import pandas as pd
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from database_models import DatabaseManager, Property
from sqlalchemy.exc import SQLAlchemyError

import send_agent_messages
from datetime import datetime
from scraper_logger import ScraperLogger

# Configuration for retry mechanism
RETRY_CONFIG = {
    'search_retries': 3,
    'search_base_delay': 1,
    'search_max_delay': 60,
    'search_backoff_factor': 2,
    'property_retries': 2,
    'property_base_delay': 0.5,
    'property_max_delay': 15,
    'property_backoff_factor': 1.5
}

# Retry decorator with exponential backoff
def retry_with_backoff(max_retries=3, base_delay=1, max_delay=60, backoff_factor=2):
    """Retry decorator with exponential backoff and jitter"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise last_exception
                    
                    # Add jitter to prevent thundering herd
                    jitter = random.uniform(0, 0.1 * delay)
                    sleep_time = min(delay + jitter, max_delay)
                    
                    print(f"  Attempt {attempt + 1} failed: {str(e)}. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    delay = min(delay * backoff_factor, max_delay)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Load configurations from the database
def load_search_configs(db_manager):
    """Load search configurations from the database"""
    try:
        configs = db_manager.get_all_search_configs(active_only=True)
        if not configs:
            print("No active search configurations found in database.")
            return []
        
        # Convert database objects to dictionary format for compatibility
        config_list = []
        for config in configs:
            config_dict = {
                'search_value': config.search_value,
                'ne_lat': config.ne_lat,
                'ne_long': config.ne_long,
                'sw_lat': config.sw_lat,
                'sw_long': config.sw_long,
                'pagination': config.pagination,
                'description': config.description
            }
            config_list.append(config_dict)
        
        print(f"Loaded {len(config_list)} active search configurations from database")
        return config_list
        
    except Exception as e:
        print(f"Error loading search configurations from database: {str(e)}")
        return []

@retry_with_backoff(max_retries=RETRY_CONFIG['search_retries'], base_delay=RETRY_CONFIG['search_base_delay'], 
                   max_delay=RETRY_CONFIG['search_max_delay'], backoff_factor=RETRY_CONFIG['search_backoff_factor'])
def process_search_config(config, proxy_url):
    """Process a single search configuration with retry mechanism"""
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
    
    # Process properties concurrently for better performance
    @retry_with_backoff(max_retries=RETRY_CONFIG['property_retries'], base_delay=RETRY_CONFIG['property_base_delay'], 
                       max_delay=RETRY_CONFIG['property_max_delay'], backoff_factor=RETRY_CONFIG['property_backoff_factor'])
    def process_property(property_info):
        try:
            property_url = "https://www.zillow.com" + property_info['detailUrl']
            data = pyzill.get_from_home_url(property_url, proxy_url)
            
            # Create a dictionary for this property
            property_dict = {
                'Address': property_info['address'],
                'Price': property_info['price'],
                'Sold_By': property_info['marketingStatusSimplifiedCd'],
                'Url': property_url
            }
            
            # Flatten attribution data into individual columns
            if 'attributionInfo' in data and data['attributionInfo']:
                for key, value in data['attributionInfo'].items():
                    # Clean the column name by removing special characters and spaces
                    clean_key = key.replace(' ', '_').replace('-', '_').replace('(', '').replace(')', '')
                    property_dict[f'Attribution_{clean_key}'] = value
            
            return property_dict
        except Exception as e:
            print(f"    Error processing property {property_info.get('address', 'unknown')}: {str(e)}")
            return None
    
    # Process properties concurrently (limit to 10 for testing, remove limit for production)
    property_limit = min(10, len(map_result))
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_property = {executor.submit(process_property, map_result[i]): i for i in range(property_limit)}
        
        for future in as_completed(future_to_property):
            try:
                property_dict = future.result()
                if property_dict:
                    properties_data.append(property_dict)
            except Exception as e:
                print(f"    Error processing property: {str(e)}")
                continue
    
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

@retry_with_backoff(max_retries=RETRY_CONFIG['search_retries'], base_delay=RETRY_CONFIG['search_base_delay'], 
                   max_delay=RETRY_CONFIG['search_max_delay'], backoff_factor=RETRY_CONFIG['search_backoff_factor'])
def process_search_with_retry(config, proxy_url):
    """Process a single search configuration with retry mechanism"""
    return process_search_config(config, proxy_url)

def main():
    """Main function to run the property scraper"""
    start_time = time.time()
    
    # Initialize logger
    with ScraperLogger() as logger:
        try:
            print("="*50)
            print("ZILLOW PROPERTY SCRAPER")
            print("="*50)
            print(f"Started at: {datetime.now()}")
            
            # Initialize database manager
            db_manager = DatabaseManager()
            logger.info("Database connection established.")
            logger.info("Data will be stored in: zillow_properties.db")
            
            # Load search configurations
            search_configs = load_search_configs(db_manager)
            
            if not search_configs:
                logger.warning("No search configurations found. Please check your database for active search configurations.")
                return
            
            # Proxy configuration
            proxy_url = pyzill.parse_proxy("76cc06db4f59a17e.shg.na.pyproxy.io", "16666",
                                           "ASDAr32-zone-resi-region-us", "Fzsdf23")
            
            # Process each search configuration separately with concurrent processing
            successful_searches = []
            total_properties_saved = 0
            total_properties_found = 0
            
            # Optimize thread count based on number of configs and system capabilities
            max_workers = min(5, len(search_configs), 10)  # Cap at 10 to avoid overwhelming the API
            logger.info(f"Using {max_workers} concurrent workers for processing")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_config = {executor.submit(process_search_with_retry, config, proxy_url): config for config in search_configs}
                
                for future in as_completed(future_to_config):
                    config = future_to_config[future]
                    try:
                        properties_data = future.result()
                        if properties_data:
                            total_properties_found += len(properties_data)
                            saved_count = save_search_to_database(properties_data, config, db_manager)
                            if saved_count > 0:
                                successful_searches.append(config['search_value'])
                                total_properties_saved += saved_count
                            
                            # Update progress in logger
                            logger.update_progress(
                                len(search_configs),
                                len(successful_searches),
                                total_properties_found,
                                total_properties_saved
                            )
                    except Exception as e:
                        logger.error(f"Error processing search '{config['search_value']}': {str(e)}")
                        continue
            
            # Summary
            logger.info(f"\n{'='*50}")
            logger.info("DATABASE STORAGE SUMMARY")
            logger.info(f"{'='*50}")
            logger.info(f"Total searches processed: {len(search_configs)}")
            logger.info(f"Successful searches: {len(successful_searches)}")
            logger.info(f"Total properties found: {total_properties_found}")
            logger.info(f"Total properties saved: {total_properties_saved}")
            
            if successful_searches:
                logger.info(f"\nSearch terms stored in database:")
                for search_term in successful_searches:
                    count = len(db_manager.get_properties_by_search_term(search_term))
                    logger.info(f"  ✓ {search_term}: {count} properties")
                
                # Show database statistics
                logger.info(f"\nDatabase Statistics:")
                all_properties = db_manager.get_all_properties()
                unique_search_terms = db_manager.get_unique_search_terms()
                logger.info(f"  Total properties in database: {len(all_properties)}")
                logger.info(f"  Unique search terms: {len(unique_search_terms)}")
                
                # Optional: Export to CSV for backup/viewing
                export_choice = input("\nWould you like to export the database to CSV files? (y/n): ").lower()
                if export_choice == 'y':
                    logger.info("\nExporting database to CSV files...")
                    exported_files = export_database_to_csv(db_manager)
                    if exported_files:
                        logger.info(f"\nExported {len(exported_files)} CSV files:")
                        for filepath in exported_files:
                            logger.info(f"  ✓ {filepath}")
            else:
                logger.warning("No data was saved to the database.")
            
            # Performance summary
            end_time = time.time()
            total_time = end_time - start_time
            logger.info(f"\n{'='*50}")
            logger.info("PERFORMANCE SUMMARY")
            logger.info(f"{'='*50}")
            logger.info(f"Total execution time: {total_time:.2f} seconds")
            if total_properties_saved > 0:
                logger.info(f"Properties processed per second: {total_properties_saved/total_time:.2f}")
                logger.info(f"Average time per property: {total_time/total_properties_saved:.2f} seconds")
            
            # Close database connection
            db_manager.close()
            logger.info("Database connection closed.")
            
            # Mark as successfully completed
            logger.complete_success(
                len(search_configs),
                len(successful_searches),
                total_properties_found,
                total_properties_saved
            )
            
            # send_agent_messages.main()
            
        except Exception as e:
            logger.complete_failure(f"Unexpected error in main function: {str(e)}")
            raise




if __name__ == "__main__":
    main()
