#!/usr/bin/env python3
"""
Management script for message templates in the database
"""
import json
from database_models import DatabaseManager

def add_message_template():
    """Add a new message template to the database"""
    print("\n=== Add New Message Template ===")
    
    # Get user input
    name = input("Enter template name (e.g., 'Initial Contact'): ").strip()
    if not name:
        print("Template name cannot be empty.")
        return
    
    print("\nEnter template text. Use variables like {agent_name}, {property_address}, {property_price}, {search_area}")
    print("Press Enter twice to finish:")
    
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    
    template_text = "\n".join(lines[:-1])  # Remove the last empty line
    
    if not template_text.strip():
        print("Template text cannot be empty.")
        return
    
    description = input("Enter description (optional): ").strip() or ""
    category = input("Enter category (e.g., 'initial', 'follow_up', 'general') [default: general]: ").strip() or "general"
    
    # Ask about available variables
    print("\nAvailable variables in your template:")
    variables = []
    if '{agent_name}' in template_text:
        variables.append('agent_name')
    if '{property_address}' in template_text:
        variables.append('property_address')
    if '{property_price}' in template_text:
        variables.append('property_price')
    if '{search_area}' in template_text:
        variables.append('search_area')
    
    if variables:
        print(f"  Detected: {', '.join(variables)}")
    else:
        print("  No standard variables detected")
    
    # Ask if this should be the default template
    set_default = input("\nSet as default template? (y/N): ").strip().lower() == 'y'
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    try:
        # Check if template already exists
        existing = db_manager.get_message_template_by_name(name)
        if existing:
            print(f"Template '{name}' already exists.")
            return
        
        # Create template data
        template_data = {
            'name': name,
            'template_text': template_text,
            'description': description,
            'category': category,
            'available_variables': json.dumps(variables),
            'is_default': set_default,
            'is_active': True
        }
        
        # Add to database
        db_manager.add_message_template(template_data)
        db_manager.commit()
        
        print(f"✓ Successfully added message template: {name}")
        if set_default:
            print("  ✓ Set as default template")
        
    except Exception as e:
        print(f"Error adding message template: {str(e)}")
        db_manager.rollback()
    
    finally:
        db_manager.close()

def view_message_templates():
    """View all message templates in the database"""
    print("\n=== View Message Templates ===")
    
    db_manager = DatabaseManager()
    
    try:
        templates = db_manager.get_all_message_templates(active_only=False)
        
        if not templates:
            print("No message templates found in database.")
            return
        
        print(f"Found {len(templates)} message template(s):\n")
        
        for i, template in enumerate(templates, 1):
            status = "Active" if template.is_active else "Inactive"
            default_flag = " (Default)" if template.is_default else ""
            print(f"{i}. {template.name}{default_flag}")
            print(f"   Status: {status}")
            print(f"   Category: {template.category}")
            if template.description:
                print(f"   Description: {template.description}")
            
            # Show available variables
            if template.available_variables:
                try:
                    variables = json.loads(template.available_variables)
                    if variables:
                        print(f"   Variables: {', '.join(variables)}")
                except json.JSONDecodeError:
                    pass
            
            print(f"   Created: {template.created_at}")
            print()
        
    except Exception as e:
        print(f"Error viewing message templates: {str(e)}")
    
    finally:
        db_manager.close()

def view_template_text():
    """View the full text of a specific template"""
    print("\n=== View Template Text ===")
    
    db_manager = DatabaseManager()
    
    try:
        templates = db_manager.get_all_message_templates(active_only=False)
        
        if not templates:
            print("No message templates found in database.")
            return
        
        print("Available templates:")
        for i, template in enumerate(templates, 1):
            default_flag = " (Default)" if template.is_default else ""
            print(f"{i}. {template.name}{default_flag}")
        
        try:
            choice = int(input("\nEnter the number of the template to view: ").strip())
            if 1 <= choice <= len(templates):
                selected_template = templates[choice - 1]
                
                print(f"\n{'='*60}")
                print(f"TEMPLATE: {selected_template.name}")
                print(f"{'='*60}")
                print(f"Category: {selected_template.category}")
                if selected_template.description:
                    print(f"Description: {selected_template.description}")
                print(f"Status: {'Active' if selected_template.is_active else 'Inactive'}")
                print(f"Default: {'Yes' if selected_template.is_default else 'No'}")
                print(f"Created: {selected_template.created_at}")
                print(f"{'='*60}")
                print("TEMPLATE TEXT:")
                print(f"{'='*60}")
                print(selected_template.template_text)
                print(f"{'='*60}")
                
            else:
                print("Invalid choice.")
                
        except ValueError:
            print("Please enter a valid number.")
        
    except Exception as e:
        print(f"Error viewing template text: {str(e)}")
    
    finally:
        db_manager.close()

def set_default_template():
    """Set a message template as the default"""
    print("\n=== Set Default Template ===")
    
    db_manager = DatabaseManager()
    
    try:
        templates = db_manager.get_all_message_templates(active_only=True)
        
        if not templates:
            print("No active message templates found in database.")
            return
        
        print("Available active templates:")
        for i, template in enumerate(templates, 1):
            default_flag = " (Current Default)" if template.is_default else ""
            print(f"{i}. {template.name}{default_flag}")
        
        try:
            choice = int(input("\nEnter the number of the template to set as default: ").strip())
            if 1 <= choice <= len(templates):
                selected_template = templates[choice - 1]
                
                success = db_manager.set_default_message_template(selected_template.name)
                if success:
                    print(f"✓ Successfully set '{selected_template.name}' as default template")
                else:
                    print(f"✗ Failed to set '{selected_template.name}' as default")
            else:
                print("Invalid choice.")
                
        except ValueError:
            print("Please enter a valid number.")
        
    except Exception as e:
        print(f"Error setting default template: {str(e)}")
    
    finally:
        db_manager.close()

def toggle_template_status():
    """Toggle a message template between active and inactive"""
    print("\n=== Toggle Template Status ===")
    
    db_manager = DatabaseManager()
    
    try:
        templates = db_manager.get_all_message_templates(active_only=False)
        
        if not templates:
            print("No message templates found in database.")
            return
        
        print("Available templates:")
        for i, template in enumerate(templates, 1):
            status = "Active" if template.is_active else "Inactive"
            default_flag = " (Default)" if template.is_default else ""
            print(f"{i}. {template.name}{default_flag} ({status})")
        
        try:
            choice = int(input("\nEnter the number of the template to toggle: ").strip())
            if 1 <= choice <= len(templates):
                selected_template = templates[choice - 1]
                
                if selected_template.is_default:
                    print(f"Cannot deactivate default template '{selected_template.name}'. Set another template as default first.")
                    return
                
                if selected_template.is_active:
                    success = db_manager.deactivate_message_template(selected_template.name)
                    if success:
                        print(f"✓ Deactivated: {selected_template.name}")
                    else:
                        print(f"✗ Failed to deactivate: {selected_template.name}")
                else:
                    success = db_manager.activate_message_template(selected_template.name)
                    if success:
                        print(f"✓ Activated: {selected_template.name}")
                    else:
                        print(f"✗ Failed to activate: {selected_template.name}")
            else:
                print("Invalid choice.")
                
        except ValueError:
            print("Please enter a valid number.")
        
    except Exception as e:
        print(f"Error toggling template status: {str(e)}")
    
    finally:
        db_manager.close()

def delete_message_template():
    """Delete a message template from the database"""
    print("\n=== Delete Message Template ===")
    
    db_manager = DatabaseManager()
    
    try:
        templates = db_manager.get_all_message_templates(active_only=False)
        
        if not templates:
            print("No message templates found in database.")
            return
        
        print("Available templates:")
        for i, template in enumerate(templates, 1):
            default_flag = " (Default)" if template.is_default else ""
            print(f"{i}. {template.name}{default_flag}")
        
        try:
            choice = int(input("\nEnter the number of the template to delete: ").strip())
            if 1 <= choice <= len(templates):
                selected_template = templates[choice - 1]
                
                if selected_template.is_default:
                    print(f"Cannot delete default template '{selected_template.name}'. Set another template as default first.")
                    return
                
                confirm = input(f"Are you sure you want to delete '{selected_template.name}'? (y/N): ").strip().lower()
                if confirm == 'y':
                    success = db_manager.delete_message_template(selected_template.name)
                    if success:
                        print(f"✓ Deleted: {selected_template.name}")
                    else:
                        print(f"✗ Failed to delete: {selected_template.name}")
                else:
                    print("Deletion cancelled.")
            else:
                print("Invalid choice.")
                
        except ValueError:
            print("Please enter a valid number.")
        
    except Exception as e:
        print(f"Error deleting message template: {str(e)}")
    
    finally:
        db_manager.close()

def main():
    """Main menu for managing message templates"""
    while True:
        print("\n" + "="*60)
        print("MESSAGE TEMPLATE MANAGER")
        print("="*60)
        print("1. View all message templates")
        print("2. View template text")
        print("3. Add new message template")
        print("4. Set default template")
        print("5. Toggle template status (active/inactive)")
        print("6. Delete message template")
        print("7. Exit")
        print("-"*60)
        
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == '1':
            view_message_templates()
        elif choice == '2':
            view_template_text()
        elif choice == '3':
            add_message_template()
        elif choice == '4':
            set_default_template()
        elif choice == '5':
            toggle_template_status()
        elif choice == '6':
            delete_message_template()
        elif choice == '7':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")

if __name__ == "__main__":
    main()
