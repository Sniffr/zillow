#!/usr/bin/env python3
"""
Management script for search configurations in the database
"""
from database_models import DatabaseManager

def add_search_config():
    """Add a new search configuration to the database"""
    print("\n=== Add New Search Configuration ===")
    
    # Get user input
    search_value = input("Enter search value (e.g., 'Single family houses in San Diego'): ").strip()
    if not search_value:
        print("Search value cannot be empty.")
        return
    
    try:
        ne_lat = float(input("Enter NE latitude (e.g., 32.8): ").strip())
        ne_long = float(input("Enter NE longitude (e.g., -117.0): ").strip())
        sw_lat = float(input("Enter SW latitude (e.g., 32.7): ").strip())
        sw_long = float(input("Enter SW longitude (e.g., -117.1): ").strip())
        pagination = int(input("Enter pagination (default 1): ").strip() or "1")
        description = input("Enter description (optional): ").strip() or ""
        
    except ValueError:
        print("Invalid numeric input. Please enter valid numbers.")
        return
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    try:
        # Check if config already exists
        existing = db_manager.get_search_config_by_value(search_value)
        if existing:
            print(f"Search configuration for '{search_value}' already exists.")
            return
        
        # Create config data
        config_data = {
            'search_value': search_value,
            'ne_lat': ne_lat,
            'ne_long': ne_long,
            'sw_lat': sw_lat,
            'sw_long': sw_long,
            'pagination': pagination,
            'description': description
        }
        
        # Add to database
        db_manager.add_search_config(config_data)
        db_manager.commit()
        
        print(f"✓ Successfully added search configuration for: {search_value}")
        
    except Exception as e:
        print(f"Error adding search configuration: {str(e)}")
        db_manager.rollback()
    
    finally:
        db_manager.close()

def view_search_configs():
    """View all search configurations in the database"""
    print("\n=== View Search Configurations ===")
    
    db_manager = DatabaseManager()
    
    try:
        configs = db_manager.get_all_search_configs(active_only=False)
        
        if not configs:
            print("No search configurations found in database.")
            return
        
        print(f"Found {len(configs)} search configuration(s):\n")
        
        for i, config in enumerate(configs, 1):
            status = "Active" if config.is_active else "Inactive"
            print(f"{i}. {config.search_value}")
            print(f"   Status: {status}")
            print(f"   Coordinates: NE({config.ne_lat}, {config.ne_long}), SW({config.sw_lat}, {config.sw_long})")
            print(f"   Pagination: {config.pagination}")
            if config.description:
                print(f"   Description: {config.description}")
            print(f"   Created: {config.created_at}")
            print()
        
    except Exception as e:
        print(f"Error viewing search configurations: {str(e)}")
    
    finally:
        db_manager.close()

def toggle_search_config():
    """Toggle a search configuration between active and inactive"""
    print("\n=== Toggle Search Configuration Status ===")
    
    db_manager = DatabaseManager()
    
    try:
        configs = db_manager.get_all_search_configs(active_only=False)
        
        if not configs:
            print("No search configurations found in database.")
            return
        
        print("Available configurations:")
        for i, config in enumerate(configs, 1):
            status = "Active" if config.is_active else "Inactive"
            print(f"{i}. {config.search_value} ({status})")
        
        try:
            choice = int(input("\nEnter the number of the configuration to toggle: ").strip())
            if 1 <= choice <= len(configs):
                selected_config = configs[choice - 1]
                
                if selected_config.is_active:
                    success = db_manager.deactivate_search_config(selected_config.search_value)
                    if success:
                        print(f"✓ Deactivated: {selected_config.search_value}")
                    else:
                        print(f"✗ Failed to deactivate: {selected_config.search_value}")
                else:
                    success = db_manager.activate_search_config(selected_config.search_value)
                    if success:
                        print(f"✓ Activated: {selected_config.search_value}")
                    else:
                        print(f"✗ Failed to activate: {selected_config.search_value}")
            else:
                print("Invalid choice.")
                
        except ValueError:
            print("Please enter a valid number.")
        
    except Exception as e:
        print(f"Error toggling search configuration: {str(e)}")
    
    finally:
        db_manager.close()

def delete_search_config():
    """Delete a search configuration from the database"""
    print("\n=== Delete Search Configuration ===")
    
    db_manager = DatabaseManager()
    
    try:
        configs = db_manager.get_all_search_configs(active_only=False)
        
        if not configs:
            print("No search configurations found in database.")
            return
        
        print("Available configurations:")
        for i, config in enumerate(configs, 1):
            status = "Active" if config.is_active else "Inactive"
            print(f"{i}. {config.search_value} ({status})")
        
        try:
            choice = int(input("\nEnter the number of the configuration to delete: ").strip())
            if 1 <= choice <= len(configs):
                selected_config = configs[choice - 1]
                
                confirm = input(f"Are you sure you want to delete '{selected_config.search_value}'? (y/N): ").strip().lower()
                if confirm == 'y':
                    success = db_manager.delete_search_config(selected_config.search_value)
                    if success:
                        print(f"✓ Deleted: {selected_config.search_value}")
                    else:
                        print(f"✗ Failed to delete: {selected_config.search_value}")
                else:
                    print("Deletion cancelled.")
            else:
                print("Invalid choice.")
                
        except ValueError:
            print("Please enter a valid number.")
        
    except Exception as e:
        print(f"Error deleting search configuration: {str(e)}")
    
    finally:
        db_manager.close()

def main():
    """Main menu for managing search configurations"""
    while True:
        print("\n" + "="*50)
        print("SEARCH CONFIGURATION MANAGER")
        print("="*50)
        print("1. View all search configurations")
        print("2. Add new search configuration")
        print("3. Toggle configuration status (active/inactive)")
        print("4. Delete search configuration")
        print("5. Exit")
        print("-"*50)
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            view_search_configs()
        elif choice == '2':
            add_search_config()
        elif choice == '3':
            toggle_search_config()
        elif choice == '4':
            delete_search_config()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main()
