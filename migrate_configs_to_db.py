#!/usr/bin/env python3
"""
Migration script to move search configurations from JSON file to database
"""
import json
import os
from datetime import datetime
from database_models import DatabaseManager

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

def migrate_configs_to_database():
    """Migrate search configurations from JSON to database"""
    config_file = 'search_configs.json'
    
    # Load existing configurations
    search_configs = load_search_configs(config_file)
    
    if not search_configs:
        print("No search configurations found in JSON file.")
        return
    
    # Initialize database manager
    db_manager = DatabaseManager()
    print("Database connection established.")
    
    # Check if configurations already exist
    existing_configs = db_manager.get_all_search_configs(active_only=False)
    existing_search_values = [config.search_value for config in existing_configs]
    
    migrated_count = 0
    skipped_count = 0
    
    for config in search_configs:
        if config['search_value'] in existing_search_values:
            print(f"Skipping '{config['search_value']}' - already exists in database")
            skipped_count += 1
            continue
        
        try:
            # Add description field if not present
            if 'description' not in config:
                config['description'] = f"Migrated from JSON config on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            db_manager.add_search_config(config)
            migrated_count += 1
            print(f"✓ Migrated: {config['search_value']}")
            
        except Exception as e:
            print(f"✗ Error migrating '{config['search_value']}': {str(e)}")
    
    # Commit all changes
    db_manager.commit()
    
    print(f"\n{'='*50}")
    print("MIGRATION SUMMARY")
    print(f"{'='*50}")
    print(f"Total configs in JSON: {len(search_configs)}")
    print(f"Migrated to database: {migrated_count}")
    print(f"Skipped (already exist): {skipped_count}")
    
    # Show final database state
    final_configs = db_manager.get_all_search_configs(active_only=False)
    print(f"\nTotal configs in database: {len(final_configs)}")
    
    if final_configs:
        print("\nSearch configurations in database:")
        for config in final_configs:
            status = "Active" if config.is_active else "Inactive"
            print(f"  ✓ {config.search_value} ({status})")
    
    # Close database connection
    db_manager.close()
    print("\nDatabase connection closed.")
    
    # Backup the original JSON file
    if migrated_count > 0:
        backup_file = f"{config_file}.backup"
        try:
            os.rename(config_file, backup_file)
            print(f"\nOriginal JSON file backed up to: {backup_file}")
        except Exception as e:
            print(f"\nWarning: Could not backup JSON file: {str(e)}")

if __name__ == "__main__":
    migrate_configs_to_database()
