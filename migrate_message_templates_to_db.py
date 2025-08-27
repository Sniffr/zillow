#!/usr/bin/env python3
"""
Migration script to move message templates from JSON config to database
"""
import json
import os
from database_models import DatabaseManager

def load_twilio_config():
    """Load Twilio configuration from JSON file"""
    config_file = 'twilio_config.json'
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{config_file}'.")
        return None

def migrate_message_templates_to_database():
    """Migrate message templates from JSON config to database"""
    print("=== Message Template Migration ===")
    
    # Load existing configuration
    config = load_twilio_config()
    
    if not config or 'message' not in config:
        print("No message templates found in twilio_config.json")
        return
    
    # Initialize database manager
    db_manager = DatabaseManager()
    print("Database connection established.")
    
    # Check if templates already exist
    existing_templates = db_manager.get_all_message_templates(active_only=False)
    existing_template_names = [template.name for template in existing_templates]
    
    migrated_count = 0
    skipped_count = 0
    
    # Define the templates to migrate
    templates_to_migrate = []
    
    # Add the main template if it exists
    if 'template' in config['message']:
        templates_to_migrate.append({
            'name': 'Main Property Template',
            'template_text': config['message']['template'],
            'description': 'Main template for contacting agents about specific properties',
            'category': 'initial',
            'available_variables': json.dumps([
                'agent_name', 'property_address', 'property_price', 'search_area'
            ]),
            'is_default': True
        })
    
    # Add the default text template if it exists
    if 'default_text' in config['message']:
        templates_to_migrate.append({
            'name': 'General Inquiry Template',
            'template_text': config['message']['default_text'],
            'description': 'General template for property inquiries',
            'category': 'general',
            'available_variables': json.dumps([
                'agent_name', 'property_address', 'property_price', 'search_area'
            ]),
            'is_default': False
        })
    
    # Add a fallback template if none exist
    if not templates_to_migrate:
        fallback_template = {
            'name': 'Default Property Template',
            'template_text': """Hello {agent_name}! 

I saw your listing for the property at {property_address} (listed at {property_price}) in the {search_area} area.

I'm very interested in learning more about this property. Could you please send me additional information and let me know when we could schedule a viewing?

Thank you!""",
            'description': 'Default template created during migration',
            'category': 'initial',
            'available_variables': json.dumps([
                'agent_name', 'property_address', 'property_price', 'search_area'
            ]),
            'is_default': True
        }
        templates_to_migrate.append(fallback_template)
    
    # Migrate each template
    for template_data in templates_to_migrate:
        if template_data['name'] in existing_template_names:
            print(f"Skipping '{template_data['name']}' - already exists in database")
            skipped_count += 1
            continue
        
        try:
            db_manager.add_message_template(template_data)
            migrated_count += 1
            print(f"✓ Migrated: {template_data['name']}")
            
        except Exception as e:
            print(f"✗ Error migrating '{template_data['name']}': {str(e)}")
    
    # Commit all changes
    db_manager.commit()
    
    print(f"\n{'='*50}")
    print("MIGRATION SUMMARY")
    print(f"{'='*50}")
    print(f"Total templates to migrate: {len(templates_to_migrate)}")
    print(f"Migrated to database: {migrated_count}")
    print(f"Skipped (already exist): {skipped_count}")
    
    # Show final database state
    final_templates = db_manager.get_all_message_templates(active_only=False)
    print(f"\nTotal templates in database: {len(final_templates)}")
    
    if final_templates:
        print("\nMessage templates in database:")
        for template in final_templates:
            status = "Active" if template.is_active else "Inactive"
            default_flag = " (Default)" if template.is_default else ""
            print(f"  ✓ {template.name}{default_flag} ({status})")
            print(f"    Category: {template.category}")
            print(f"    Description: {template.description}")
            print()
    
    # Close database connection
    db_manager.close()
    print("Database connection closed.")
    
    # Create a backup of the original config
    if migrated_count > 0:
        backup_file = 'twilio_config.json.backup'
        try:
            with open(backup_file, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"\nOriginal config backed up to: {backup_file}")
        except Exception as e:
            print(f"\nWarning: Could not backup config file: {str(e)}")

if __name__ == "__main__":
    migrate_message_templates_to_database()
