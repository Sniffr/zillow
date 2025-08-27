"""
Utility script to view and manage the Zillow properties database
"""
from database_models import DatabaseManager, Property
import pandas as pd
from datetime import datetime
import sys

def display_menu():
    """Display the main menu"""
    print("\n" + "="*60)
    print("ZILLOW PROPERTIES DATABASE VIEWER")
    print("="*60)
    print("1. View all properties")
    print("2. View properties by search term")
    print("3. View database statistics")
    print("4. Export all data to CSV")
    print("5. Export specific search term to CSV")
    print("6. Delete properties by search term")
    print("7. Clear entire database")
    print("8. Exit")
    print("-"*60)

def view_all_properties(db_manager):
    """View all properties in the database"""
    properties = db_manager.get_all_properties()
    if not properties:
        print("\nNo properties found in the database.")
        return
    
    print(f"\nTotal properties: {len(properties)}")
    print("-"*80)
    
    for prop in properties[:10]:  # Show first 10
        print(f"ID: {prop.id}")
        print(f"Search Term: {prop.search_term}")
        print(f"Address: {prop.address}")
        print(f"Price: {prop.price}")
        print(f"Status: {prop.sold_by}")
        print(f"Created: {prop.created_at}")
        print("-"*80)
    
    if len(properties) > 10:
        print(f"... and {len(properties) - 10} more properties")

def view_by_search_term(db_manager):
    """View properties filtered by search term"""
    search_terms = db_manager.get_unique_search_terms()
    
    if not search_terms:
        print("\nNo search terms found in the database.")
        return
    
    print("\nAvailable search terms:")
    for i, term in enumerate(search_terms, 1):
        count = len(db_manager.get_properties_by_search_term(term))
        print(f"{i}. {term} ({count} properties)")
    
    try:
        choice = int(input("\nSelect a search term (number): ")) - 1
        if 0 <= choice < len(search_terms):
            selected_term = search_terms[choice]
            properties = db_manager.get_properties_by_search_term(selected_term)
            
            print(f"\nProperties for '{selected_term}': {len(properties)} found")
            print("-"*80)
            
            for prop in properties[:5]:  # Show first 5
                print(f"Address: {prop.address}")
                print(f"Price: {prop.price}")
                print(f"URL: {prop.url}")
                print("-"*80)
            
            if len(properties) > 5:
                print(f"... and {len(properties) - 5} more properties")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")

def view_statistics(db_manager):
    """View database statistics"""
    all_properties = db_manager.get_all_properties()
    search_terms = db_manager.get_unique_search_terms()
    
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    print(f"Total properties: {len(all_properties)}")
    print(f"Unique search terms: {len(search_terms)}")
    
    if search_terms:
        print("\nProperties per search term:")
        for term in search_terms:
            count = len(db_manager.get_properties_by_search_term(term))
            print(f"  • {term}: {count} properties")
    
    if all_properties:
        # Calculate price statistics
        prices = []
        for prop in all_properties:
            if prop.price:
                # Extract numeric price (remove $ and commas)
                price_str = prop.price.replace('$', '').replace(',', '')
                try:
                    prices.append(float(price_str))
                except ValueError:
                    pass
        
        if prices:
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            
            print(f"\nPrice Statistics:")
            print(f"  Average: ${avg_price:,.2f}")
            print(f"  Minimum: ${min_price:,.2f}")
            print(f"  Maximum: ${max_price:,.2f}")

def export_all_to_csv(db_manager):
    """Export all data to a CSV file"""
    properties = db_manager.get_all_properties()
    if not properties:
        print("\nNo properties to export.")
        return
    
    data = []
    for prop in properties:
        prop_dict = {
            'id': prop.id,
            'search_term': prop.search_term,
            'address': prop.address,
            'price': prop.price,
            'sold_by': prop.sold_by,
            'url': prop.url,
            'ne_lat': prop.ne_lat,
            'ne_long': prop.ne_long,
            'sw_lat': prop.sw_lat,
            'sw_long': prop.sw_long,
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
    
    df = pd.DataFrame(data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"all_properties_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"\nExported {len(properties)} properties to {filename}")

def export_by_search_term(db_manager):
    """Export properties for a specific search term to CSV"""
    search_terms = db_manager.get_unique_search_terms()
    
    if not search_terms:
        print("\nNo search terms found in the database.")
        return
    
    print("\nAvailable search terms:")
    for i, term in enumerate(search_terms, 1):
        count = len(db_manager.get_properties_by_search_term(term))
        print(f"{i}. {term} ({count} properties)")
    
    try:
        choice = int(input("\nSelect a search term to export (number): ")) - 1
        if 0 <= choice < len(search_terms):
            selected_term = search_terms[choice]
            properties = db_manager.get_properties_by_search_term(selected_term)
            
            if properties:
                data = []
                for prop in properties:
                    prop_dict = {
                        'address': prop.address,
                        'price': prop.price,
                        'sold_by': prop.sold_by,
                        'url': prop.url,
                        'created_at': prop.created_at
                    }
                    # Add attribution fields
                    for col in Property.__table__.columns:
                        if col.name.startswith('attribution_') and col.name != 'attribution_extra':
                            value = getattr(prop, col.name)
                            if value:
                                prop_dict[col.name] = value
                    data.append(prop_dict)
                
                df = pd.DataFrame(data)
                clean_name = selected_term.replace(' ', '_').replace('-', '_')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{clean_name}_{timestamp}.csv"
                df.to_csv(filename, index=False)
                print(f"\nExported {len(properties)} properties to {filename}")
            else:
                print(f"\nNo properties found for '{selected_term}'")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")

def delete_by_search_term(db_manager):
    """Delete properties for a specific search term"""
    search_terms = db_manager.get_unique_search_terms()
    
    if not search_terms:
        print("\nNo search terms found in the database.")
        return
    
    print("\nAvailable search terms:")
    for i, term in enumerate(search_terms, 1):
        count = len(db_manager.get_properties_by_search_term(term))
        print(f"{i}. {term} ({count} properties)")
    
    try:
        choice = int(input("\nSelect a search term to delete (number): ")) - 1
        if 0 <= choice < len(search_terms):
            selected_term = search_terms[choice]
            count = len(db_manager.get_properties_by_search_term(selected_term))
            
            confirm = input(f"\nAre you sure you want to delete {count} properties for '{selected_term}'? (y/n): ")
            if confirm.lower() == 'y':
                db_manager.delete_properties_by_search_term(selected_term)
                print(f"\nDeleted {count} properties for '{selected_term}'")
            else:
                print("Deletion cancelled.")
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")

def clear_database(db_manager):
    """Clear the entire database"""
    all_properties = db_manager.get_all_properties()
    count = len(all_properties)
    
    if count == 0:
        print("\nDatabase is already empty.")
        return
    
    confirm = input(f"\nAre you sure you want to delete ALL {count} properties? This cannot be undone! (yes/no): ")
    if confirm.lower() == 'yes':
        for prop in all_properties:
            db_manager.session.delete(prop)
        db_manager.commit()
        print(f"\nDeleted all {count} properties from the database.")
    else:
        print("Database clear cancelled.")

def main():
    """Main function"""
    print("Connecting to database...")
    db_manager = DatabaseManager()
    print("Connected to zillow_properties.db")
    
    while True:
        display_menu()
        choice = input("Enter your choice (1-8): ")
        
        if choice == '1':
            view_all_properties(db_manager)
        elif choice == '2':
            view_by_search_term(db_manager)
        elif choice == '3':
            view_statistics(db_manager)
        elif choice == '4':
            export_all_to_csv(db_manager)
        elif choice == '5':
            export_by_search_term(db_manager)
        elif choice == '6':
            delete_by_search_term(db_manager)
        elif choice == '7':
            clear_database(db_manager)
        elif choice == '8':
            print("\nClosing database connection...")
            db_manager.close()
            print("Goodbye!")
            sys.exit(0)
        else:
            print("\nInvalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
