"""
Flask web application for Zillow Property Manager
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database_models import DatabaseManager, Property, SearchConfig, MessageTemplate
import subprocess
import threading
import os
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import schedule

app = Flask(__name__)
app.secret_key = 'zillow_property_manager_secret_key_2024'

# Global variable to track scraper status
scraper_status_data = {
    'running': False,
    'message': '',
    'last_run': None,
    'next_run': None,
    'total_runs': 0,
    'successful_runs': 0,
    'failed_runs': 0
}

# Scraper scheduler thread
scheduler_thread = None
scheduler_running = False

def run_scraper_background():
    """Run the scraper in the background"""
    global scraper_status_data
    
    try:
        scraper_status_data['running'] = True
        scraper_status_data['message'] = 'Scraper started'
        scraper_status_data['last_run'] = datetime.now()
        scraper_status_data['total_runs'] += 1
        
        print(f"[{datetime.now()}] Starting scheduled scraper execution...")
        
        # Run the scraper script
        result = subprocess.run(['python', 'get_listing_and_agent.py'], 
                             capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            scraper_status_data['message'] = 'Scraper completed successfully'
            scraper_status_data['successful_runs'] += 1
            print(f"[{datetime.now()}] Scraper completed successfully")
        else:
            scraper_status_data['message'] = f'Scraper failed with error: {result.stderr}'
            scraper_status_data['failed_runs'] += 1
            print(f"[{datetime.now()}] Scraper failed: {result.stderr}")
        
    except Exception as e:
        scraper_status_data['message'] = f'Error running scraper: {str(e)}'
        scraper_status_data['failed_runs'] += 1
        print(f"[{datetime.now()}] Error running scraper: {str(e)}")
    finally:
        scraper_status_data['running'] = False
        # Schedule next run
        schedule_next_run()

def schedule_next_run():
    """Schedule the next scraper run"""
    global scraper_status_data
    next_run = datetime.now() + timedelta(minutes=10)
    scraper_status_data['next_run'] = next_run
    print(f"[{datetime.now()}] Next scraper run scheduled for: {next_run}")

def scheduler_worker():
    """Background worker for the scheduler"""
    global scheduler_running
    
    print(f"[{datetime.now()}] Scraper scheduler started")
    
    while scheduler_running:
        try:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"[{datetime.now()}] Scheduler error: {str(e)}")
            time.sleep(60)  # Wait longer on error
    
    print(f"[{datetime.now()}] Scraper scheduler stopped")

def start_scheduler():
    """Start the scraper scheduler"""
    global scheduler_thread, scheduler_running, scraper_status_data
    
    if scheduler_running:
        print("Scheduler already running")
        return
    
    # Schedule scraper to run every 10 minutes
    schedule.every(10).minutes.do(run_scraper_background)
    
    # Start scheduler thread
    scheduler_running = True
    scheduler_thread = threading.Thread(target=scheduler_worker, daemon=True)
    scheduler_thread.start()
    
    print(f"[{datetime.now()}] Scraper scheduler started - will run every 10 minutes")
    
    # Schedule first run
    schedule_next_run()

def stop_scheduler():
    """Stop the scraper scheduler"""
    global scheduler_running, scheduler_thread
    
    if not scheduler_running:
        print("Scheduler not running")
        return
    
    scheduler_running = False
    if scheduler_thread and scheduler_thread.is_alive():
        scheduler_thread.join(timeout=5)
    
    print(f"[{datetime.now()}] Scraper scheduler stopped")

def initialize_app():
    """Initialize the application on first request"""
    print(f"[{datetime.now()}] Initializing Zillow Property Manager...")
    
    # Start the scraper scheduler
    start_scheduler()
    
    # Run scraper immediately on startup
    print(f"[{datetime.now()}] Running initial scraper execution...")
    initial_thread = threading.Thread(target=run_scraper_background, daemon=True)
    initial_thread.start()
    
    print(f"[{datetime.now()}] Application initialization complete")

# Initialize the app when it's created
def create_app():
    """Create and configure the Flask application"""
    initialize_app()
    return app

# Don't initialize here - it will be done when the app starts

@app.teardown_appcontext
def cleanup_app(exception=None):
    """Cleanup when the application context is torn down"""
    if exception:
        print(f"[{datetime.now()}] Application error: {str(exception)}")

@app.route('/')
def index():
    """Main dashboard page"""
    db_manager = DatabaseManager()
    
    # Get basic statistics
    total_properties = len(db_manager.get_all_properties())
    search_terms = db_manager.get_unique_search_terms()
    total_searches = len(search_terms)
    
    # Get properties with phone numbers for messaging
    properties_with_phones = 0
    unique_phones = set()
    
    for prop in db_manager.get_all_properties():
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
    
    db_manager.close()
    
    return render_template('index.html', 
                         total_properties=total_properties,
                         total_searches=total_searches,
                         properties_with_phones=properties_with_phones,
                         unique_phones=len(unique_phones),
                         scraper_status=scraper_status_data)

@app.route('/properties')
def properties():
    """Properties page with DataTable"""
    return render_template('properties.html')

@app.route('/toast_demo')
def toast_demo():
    """Toast notification demo page"""
    return render_template('toast_demo.html')

@app.route('/api/properties')
def api_properties():
    """API endpoint to get properties for DataTable"""
    db_manager = DatabaseManager()
    
    # Get all properties
    properties = db_manager.get_all_properties()
    
    # Convert to list of dictionaries for DataTable
    data = []
    for prop in properties:
        # Get phone numbers
        phones = []
        if prop.attribution_agent_phone_number:
            phones.append(f"Agent: {prop.attribution_agent_phone_number}")
        if prop.attribution_broker_phone_number:
            phones.append(f"Broker: {prop.attribution_broker_phone_number}")
        if prop.attribution_co_agent_number:
            phones.append(f"Co-Agent: {prop.attribution_co_agent_number}")
        
        phone_text = "<br>".join(phones) if phones else "No phone"
        
        # Get agent info
        agent_info = []
        if prop.attribution_agent_name:
            agent_info.append(prop.attribution_agent_name)
        if prop.attribution_agent_email:
            agent_info.append(prop.attribution_agent_email)
        
        agent_text = "<br>".join(agent_info) if agent_info else "No agent info"
        
        data.append({
            'id': prop.id,
            'search_term': prop.search_term,
            'address': prop.address,
            'price': prop.price,
            'sold_by': prop.sold_by,
            'url': f'<a href="{prop.url}" target="_blank">View</a>',
            'agent_info': agent_text,
            'phone_numbers': phone_text,
            'created_at': prop.created_at.strftime('%Y-%m-%d %H:%M') if prop.created_at else '',
            'actions': f'''
                <button class="btn btn-sm btn-primary" onclick="viewProperty({prop.id})">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-success" onclick="sendMessage({prop.id})">
                    <i class="fas fa-comment"></i>
                </button>
            '''
        })
    
    db_manager.close()
    
    return jsonify({
        'data': data
    })

@app.route('/property/<int:property_id>')
def view_property(property_id):
    """View detailed property information"""
    db_manager = DatabaseManager()
    property_obj = db_manager.session.query(Property).get(property_id)
    
    if not property_obj:
        flash('Property not found', 'error')
        return redirect(url_for('properties'))
    
    # Get all attribution fields
    attribution_data = {}
    for column in Property.__table__.columns:
        if column.name.startswith('attribution_'):
            value = getattr(property_obj, column.name)
            if value:
                field_name = column.name.replace('attribution_', '').replace('_', ' ').title()
                attribution_data[field_name] = value
    
    db_manager.close()
    
    return render_template('property_detail.html', 
                         property=property_obj, 
                         attribution_data=attribution_data)

@app.route('/run_scraper', methods=['POST'])
def run_scraper():
    """Run the property scraper"""
    global scraper_status
    
    if scraper_status['running']:
        return jsonify({'success': False, 'message': 'Scraper is already running'})
    
    scraper_status['running'] = True
    scraper_status['message'] = 'Starting scraper...'
    
    def run_scraper_thread():
        global scraper_status
        try:
            # Run the scraper script
            result = subprocess.run(['python', 'get_listing_and_agent.py'], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                scraper_status['message'] = 'Scraper completed successfully!'
                # Log success for debugging
                print(f"Scraper completed successfully at {datetime.now()}")
            else:
                scraper_status['message'] = f'Scraper failed: {result.stderr}'
                # Log error for debugging
                print(f"Scraper failed at {datetime.now()}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            scraper_status['message'] = 'Scraper timed out after 5 minutes'
            print(f"Scraper timed out at {datetime.now()}")
        except Exception as e:
            scraper_status['message'] = f'Error running scraper: {str(e)}'
            print(f"Scraper error at {datetime.now()}: {str(e)}")
        finally:
            scraper_status['running'] = False
            scraper_status['last_run'] = datetime.now()
    
    # Run scraper in background thread
    thread = threading.Thread(target=run_scraper_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Scraper started successfully'})

@app.route('/send_messages', methods=['POST'])
def send_messages():
    """Send messages to agents"""
    try:
        # Run the messaging script
        result = subprocess.run(['python', 'send_agent_messages.py'], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            flash('Messages sent successfully!', 'success')
        else:
            flash(f'Error sending messages: {result.stderr}', 'error')
            
    except subprocess.TimeoutExpired:
        flash('Message sending timed out', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('index'))

# Removed duplicate route - see below for the complete implementation

@app.route('/export_csv')
def export_csv():
    """Export all properties to CSV"""
    db_manager = DatabaseManager()
    properties = db_manager.get_all_properties()
    
    if not properties:
        flash('No properties to export', 'error')
        return redirect(url_for('properties'))
    
    # Convert to DataFrame
    data = []
    for prop in properties:
        prop_dict = {
            'ID': prop.id,
            'Search Term': prop.search_term,
            'Address': prop.address,
            'Price': prop.price,
            'Sold By': prop.sold_by,
            'URL': prop.url,
            'Agent Name': prop.attribution_agent_name,
            'Agent Email': prop.attribution_agent_email,
            'Agent Phone': prop.attribution_agent_phone_number,
            'Broker Name': prop.attribution_broker_name,
            'Broker Phone': prop.attribution_broker_phone_number,
            'Created At': prop.created_at.strftime('%Y-%m-%d %H:%M') if prop.created_at else '',
        }
        data.append(prop_dict)
    
    df = pd.DataFrame(data)
    
    # Create CSV file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"zillow_properties_{timestamp}.csv"
    filepath = os.path.join('static', 'exports', filename)
    
    # Ensure exports directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    df.to_csv(filepath, index=False)
    
    db_manager.close()
    
    flash(f'CSV exported successfully: {filename}', 'success')
    return redirect(url_for('properties'))

# Search Configuration Management Routes
@app.route('/search_configs')
def search_configs():
    """Search configurations management page"""
    return render_template('search_configs.html')

@app.route('/api/search_configs')
def api_search_configs():
    """API endpoint to get search configurations for DataTable"""
    db_manager = DatabaseManager()
    
    # Get all search configurations
    configs = db_manager.get_all_search_configs(active_only=False)
    
    # Convert to list of dictionaries for DataTable
    data = []
    for config in configs:
        data.append({
            'id': config.id,
            'search_value': config.search_value,
            'ne_lat': config.ne_lat,
            'ne_long': config.ne_long,
            'sw_lat': config.sw_lat,
            'sw_long': config.sw_long,
            'pagination': config.pagination,
            'description': config.description or '',
            'is_active': 'Active' if config.is_active else 'Inactive',
            'created_at': config.created_at.strftime('%Y-%m-%d %H:%M') if config.created_at else '',
            'actions': f'''
                <button class="btn btn-sm btn-primary" onclick="editSearchConfig({config.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-{"warning" if config.is_active else "success"}" onclick="toggleSearchConfig({config.id}, {config.is_active})">
                    <i class="fas fa-{"pause" if config.is_active else "play"}"></i>
                </button>
                <button class="btn btn-sm btn-info" onclick="setDefaultSearchConfig({config.id})">
                    <i class="fas fa-star"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteSearchConfig({config.id})">
                    <i class="fas fa-trash"></i>
                </button>
            '''
        })
    
    db_manager.close()
    
    return jsonify({
        'data': data
    })

@app.route('/api/search_configs', methods=['POST'])
def api_create_search_config():
    """Create a new search configuration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['search_value', 'ne_lat', 'ne_long', 'sw_lat', 'sw_long']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        db_manager = DatabaseManager()
        
        # Check if search value already exists
        existing = db_manager.get_search_config_by_value(data['search_value'])
        if existing:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Search configuration with this value already exists'}), 400
        
        # Create config data
        config_data = {
            'search_value': data['search_value'],
            'ne_lat': float(data['ne_lat']),
            'ne_long': float(data['ne_long']),
            'sw_lat': float(data['sw_lat']),
            'sw_long': float(data['sw_long']),
            'pagination': int(data.get('pagination', 1)),
            'description': data.get('description', ''),
            'is_active': True
        }
        
        db_manager.add_search_config(config_data)
        db_manager.commit()
        db_manager.close()
        
        return jsonify({'success': True, 'message': 'Search configuration created successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating search configuration: {str(e)}'}), 500

@app.route('/api/search_configs/<int:config_id>', methods=['PUT'])
def api_update_search_config(config_id):
    """Update an existing search configuration"""
    try:
        data = request.get_json()
        
        db_manager = DatabaseManager()
        config = db_manager.session.query(SearchConfig).get(config_id)
        
        if not config:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Search configuration not found'}), 404
        
        # Update fields
        if 'search_value' in data:
            config.search_value = data['search_value']
        if 'ne_lat' in data:
            config.ne_lat = float(data['ne_lat'])
        if 'ne_long' in data:
            config.ne_long = float(data['ne_long'])
        if 'sw_lat' in data:
            config.sw_lat = float(data['sw_lat'])
        if 'sw_long' in data:
            config.sw_long = float(data['sw_long'])
        if 'pagination' in data:
            config.pagination = int(data['pagination'])
        if 'description' in data:
            config.description = data['description']
        
        db_manager.commit()
        db_manager.close()
        
        return jsonify({'success': True, 'message': 'Search configuration updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating search configuration: {str(e)}'}), 500

@app.route('/api/search_configs/<int:config_id>', methods=['DELETE'])
def api_delete_search_config(config_id):
    """Delete a search configuration"""
    try:
        db_manager = DatabaseManager()
        config = db_manager.session.query(SearchConfig).get(config_id)
        
        if not config:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Search configuration not found'}), 404
        
        db_manager.session.delete(config)
        db_manager.commit()
        db_manager.close()
        
        return jsonify({'success': True, 'message': 'Search configuration deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting search configuration: {str(e)}'}), 500

@app.route('/api/search_configs/<int:config_id>/toggle', methods=['POST'])
def api_toggle_search_config(config_id):
    """Toggle search configuration active/inactive status"""
    try:
        db_manager = DatabaseManager()
        config = db_manager.session.query(SearchConfig).get(config_id)
        
        if not config:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Search configuration not found'}), 404
        
        if config.is_active:
            db_manager.deactivate_search_config(config.search_value)
            message = 'Search configuration deactivated'
        else:
            db_manager.activate_search_config(config.search_value)
            message = 'Search configuration activated'
        
        db_manager.close()
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error toggling search configuration: {str(e)}'}), 500

# Message Template Management Routes
@app.route('/message_templates')
def message_templates():
    """Message templates management page"""
    return render_template('message_templates.html')

@app.route('/api/message_templates')
def api_message_templates():
    """API endpoint to get message templates for DataTable"""
    db_manager = DatabaseManager()
    
    # Get all message templates
    templates = db_manager.get_all_message_templates(active_only=False)
    
    # Convert to list of dictionaries for DataTable
    data = []
    for template in templates:
        data.append({
            'id': template.id,
            'name': template.name,
            'category': template.category,
            'description': template.description or '',
            'is_default': 'Yes' if template.is_default else 'No',
            'is_active': 'Active' if template.is_active else 'Inactive',
            'created_at': template.created_at.strftime('%Y-%m-%d %H:%M') if template.created_at else '',
            'actions': f'''
                <button class="btn btn-sm btn-primary" onclick="editMessageTemplate({template.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-info" onclick="viewMessageTemplate({template.id})">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-{"warning" if template.is_active else "success"}" onclick="toggleMessageTemplate({template.id}, {template.is_active})" {"disabled" if template.is_default else ""}>
                    <i class="fas fa-{"pause" if template.is_active else "play"}"></i>
                </button>
                <button class="btn btn-sm btn-success" onclick="setDefaultMessageTemplate({template.id})" {"disabled" if template.is_default else ""}>
                    <i class="fas fa-star"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteMessageTemplate({template.id})" {"disabled" if template.is_default else ""}>
                    <i class="fas fa-trash"></i>
                </button>
            '''
        })
    
    db_manager.close()
    
    return jsonify({
        'data': data
    })

@app.route('/api/message_templates', methods=['POST'])
def api_create_message_template():
    """Create a new message template"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'template_text']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
        
        db_manager = DatabaseManager()
        
        # Check if template name already exists
        existing = db_manager.get_message_template_by_name(data['name'])
        if existing:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Message template with this name already exists'}), 400
        
        # Create template data
        template_data = {
            'name': data['name'],
            'template_text': data['template_text'],
            'description': data.get('description', ''),
            'category': data.get('category', 'general'),
            'available_variables': data.get('available_variables', '[]'),
            'is_default': data.get('is_default', False),
            'is_active': True
        }
        
        db_manager.add_message_template(template_data)
        db_manager.commit()
        db_manager.close()
        
        return jsonify({'success': True, 'message': 'Message template created successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error creating message template: {str(e)}'}), 500

@app.route('/api/message_templates/<int:template_id>', methods=['PUT'])
def api_update_message_template(template_id):
    """Update an existing message template"""
    try:
        data = request.get_json()
        
        db_manager = DatabaseManager()
        template = db_manager.session.query(MessageTemplate).get(template_id)
        
        if not template:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Message template not found'}), 404
        
        # Update fields
        if 'name' in data:
            template.name = data['name']
        if 'template_text' in data:
            template.template_text = data['template_text']
        if 'description' in data:
            template.description = data['description']
        if 'category' in data:
            template.category = data['category']
        if 'available_variables' in data:
            template.available_variables = data['available_variables']
        
        db_manager.commit()
        db_manager.close()
        
        return jsonify({'success': True, 'message': 'Message template updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating message template: {str(e)}'}), 500

@app.route('/api/message_templates/<int:template_id>', methods=['DELETE'])
def api_delete_message_template(template_id):
    """Delete a message template"""
    try:
        db_manager = DatabaseManager()
        template = db_manager.session.query(MessageTemplate).get(template_id)
        
        if not template:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Message template not found'}), 404
        
        if template.is_default:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Cannot delete default template. Set another template as default first.'}), 400
        
        db_manager.session.delete(template)
        db_manager.commit()
        db_manager.close()
        
        return jsonify({'success': True, 'message': 'Message template deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting message template: {str(e)}'}), 500

@app.route('/api/message_templates/<int:template_id>/toggle', methods=['POST'])
def api_toggle_message_template(template_id):
    """Toggle message template active/inactive status"""
    try:
        db_manager = DatabaseManager()
        template = db_manager.session.query(MessageTemplate).get(template_id)
        
        if not template:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Message template not found'}), 404
        
        if template.is_default:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Cannot deactivate default template. Set another template as default first.'}), 400
        
        if template.is_active:
            db_manager.deactivate_message_template(template.name)
            message = 'Message template deactivated'
        else:
            db_manager.activate_message_template(template.name)
            message = 'Message template activated'
        
        db_manager.close()
        
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error toggling message template: {str(e)}'}), 500

@app.route('/api/message_templates/<int:template_id>/set_default', methods=['POST'])
def api_set_default_message_template(template_id):
    """Set a message template as the default"""
    try:
        db_manager = DatabaseManager()
        template = db_manager.session.query(MessageTemplate).get(template_id)
        
        if not template:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Message template not found'}), 404
        
        if not template.is_active:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Cannot set inactive template as default'}), 400
        
        # Get template name before closing session
        template_name = template.name
        
        success = db_manager.set_default_message_template(template_name)
        db_manager.close()
        
        if success:
            return jsonify({'success': True, 'message': f'"{template_name}" set as default template'})
        else:
            return jsonify({'success': False, 'message': 'Failed to set template as default'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error setting default template: {str(e)}'}), 500

@app.route('/api/message_templates/<int:template_id>')
def api_get_message_template(template_id):
    """Get a specific message template"""
    try:
        db_manager = DatabaseManager()
        template = db_manager.session.query(MessageTemplate).get(template_id)
        
        if not template:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Message template not found'}), 404
        
        template_data = {
            'id': template.id,
            'name': template.name,
            'template_text': template.template_text,
            'description': template.description,
            'category': template.category,
            'available_variables': template.available_variables,
            'is_default': template.is_default,
            'is_active': template.is_active,
            'created_at': template.created_at.strftime('%Y-%m-%d %H:%M') if template.created_at else ''
        }
        
        db_manager.close()
        
        return jsonify({'success': True, 'data': template_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting message template: {str(e)}'}), 500

@app.route('/scraper_status')
def scraper_status():
    """Scraper status page"""
    return render_template('scraper_status.html')

@app.route('/api/scraper_status')
def api_scraper_status():
    """Get current scraper status and statistics"""
    try:
        db_manager = DatabaseManager()
        
        # Get basic statistics
        total_properties = len(db_manager.get_all_properties())
        
        # Count log files
        log_dir = 'logs'
        log_file_count = 0
        if os.path.exists(log_dir):
            log_file_count = len([f for f in os.listdir(log_dir) if f.endswith('.log')])
        
        # Determine scraper status based on log files
        status = 'Idle'
        last_run = None
        
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            if log_files:
                # Get the most recent log file
                latest_log = max(log_files, key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
                latest_log_path = os.path.join(log_dir, latest_log)
                
                # Check if scraper is currently running by looking for "STARTED" vs "COMPLETED"
                try:
                    with open(latest_log_path, 'r') as f:
                        content = f.read()
                        if 'ZILLOW SCRAPER STARTED' in content and 'ZILLOW SCRAPER COMPLETED' not in content:
                            # Check if it's an error by looking for specific error patterns
                            if 'ZILLOW SCRAPER FAILED' in content or 'ERROR' in content.upper():
                                status = 'Error'
                            else:
                                status = 'Running'
                        elif 'ZILLOW SCRAPER COMPLETED' in content:
                            status = 'Completed'
                        elif 'ZILLOW SCRAPER FAILED' in content:
                            status = 'Error'
                        elif 'ERROR' in content.upper():
                            status = 'Error'
                        
                        # Extract last run time
                        lines = content.split('\n')
                        for line in lines:
                            if 'ZILLOW SCRAPER STARTED' in line:
                                # Extract timestamp from the line
                                if ' - ' in line:
                                    timestamp_str = line.split(' - ')[0]
                                    try:
                                        last_run = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f').strftime('%Y-%m-%d %H:%M:%S')
                                    except:
                                        last_run = timestamp_str
                                break
                except Exception as e:
                    print(f"Error reading log file: {e}")
        
        db_manager.close()
        
        return jsonify({
            'success': True,
            'data': {
                'status': status,
                'last_run': last_run,
                'total_properties': total_properties,
                'log_file_count': log_file_count,
                'scheduler_status': {
                    'running': scraper_status_data['running'],
                    'next_run': scraper_status_data['next_run'].strftime('%Y-%m-%d %H:%M:%S') if scraper_status_data['next_run'] else None,
                    'total_runs': scraper_status_data['total_runs'],
                    'successful_runs': scraper_status_data['successful_runs'],
                    'failed_runs': scraper_status_data['failed_runs']
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting scraper status: {str(e)}'}), 500

@app.route('/api/log_files')
def api_log_files():
    """Get list of log files"""
    try:
        log_dir = 'logs'
        log_files = []
        
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(log_dir, filename)
                    file_stat = os.stat(filepath)
                    
                    # Determine status based on log content
                    status = 'Unknown'
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            if 'ZILLOW SCRAPER STARTED' in content and 'ZILLOW SCRAPER COMPLETED' not in content:
                                # Check if it's an error by looking for specific error patterns
                                if 'ZILLOW SCRAPER FAILED' in content or 'ERROR' in content.upper():
                                    status = 'Error'
                                else:
                                    status = 'Running'
                            elif 'ZILLOW SCRAPER COMPLETED' in content:
                                status = 'Success'
                            elif 'ZILLOW SCRAPER FAILED' in content:
                                status = 'Error'
                            elif 'ERROR' in content.upper():
                                status = 'Error'
                    except:
                        status = 'Unknown'
                    
                    log_files.append({
                        'filename': filename,
                        'size': f"{file_stat.st_size / 1024:.1f} KB",
                        'last_modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'status': status,
                        'actions': f'''
                            <button class="btn btn-sm btn-primary" onclick="viewLogFile('{filename}')">
                                <i class="fas fa-eye"></i> View
                            </button>
                            <button class="btn btn-sm btn-outline-danger ms-1" onclick="deleteLogFile('{filename}')">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        '''
                    })
        
        # Sort by last modified date (newest first)
        log_files.sort(key=lambda x: x['last_modified'], reverse=True)
        
        return jsonify({'success': True, 'data': log_files})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting log files: {str(e)}'}), 500

@app.route('/api/log_files/<filename>/content')
def api_log_file_content(filename):
    """Get content of a specific log file"""
    try:
        # Security check to prevent directory traversal
        if '..' in filename or '/' in filename:
            return jsonify({'success': False, 'message': 'Invalid filename'}), 400
        
        log_dir = 'logs'
        filepath = os.path.join(log_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'message': 'Log file not found'}), 404
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'data': {
                'content': content,
                'filename': filename
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error reading log file: {str(e)}'}), 500

@app.route('/api/log_files/<filename>/download')
def api_download_log_file(filename):
    """Download a specific log file"""
    try:
        # Security check to prevent directory traversal
        if '..' in filename or '/' in filename:
            return jsonify({'success': False, 'message': 'Invalid filename'}), 400
        
        log_dir = 'logs'
        filepath = os.path.join(log_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'message': 'Log file not found'}), 404
        
        from flask import send_file
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error downloading log file: {str(e)}'}), 500

@app.route('/api/log_files/<filename>', methods=['DELETE'])
def api_delete_log_file(filename):
    """Delete a specific log file"""
    try:
        # Security check to prevent directory traversal
        if '..' in filename or '/' in filename:
            return jsonify({'success': False, 'message': 'Invalid filename'}), 400
        
        log_dir = 'logs'
        filepath = os.path.join(log_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'message': 'Log file not found'}), 404
        
        os.remove(filepath)
        
        return jsonify({'success': True, 'message': 'Log file deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting log file: {str(e)}'}), 500

@app.route('/api/run_scraper', methods=['POST'])
def api_run_scraper():
    """Run the Zillow scraper manually"""
    try:
        # Check if scraper is already running
        if scraper_status_data['running']:
            return jsonify({'success': False, 'message': 'Scraper is already running'}), 400
        
        # Start scraper in background thread
        thread = threading.Thread(target=run_scraper_background)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': 'Scraper started successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting scraper: {str(e)}'}), 500

@app.route('/api/scheduler/start', methods=['POST'])
def api_start_scheduler():
    """Start the scraper scheduler"""
    try:
        if scheduler_running:
            return jsonify({'success': False, 'message': 'Scheduler is already running'}), 400
        
        start_scheduler()
        return jsonify({'success': True, 'message': 'Scheduler started successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting scheduler: {str(e)}'}), 500

@app.route('/api/scheduler/stop', methods=['POST'])
def api_stop_scheduler():
    """Stop the scraper scheduler"""
    try:
        if not scheduler_running:
            return jsonify({'success': False, 'message': 'Scheduler is not running'}), 400
        
        stop_scheduler()
        return jsonify({'success': True, 'message': 'Scheduler stopped successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error stopping scheduler: {str(e)}'}), 500

@app.route('/api/scheduler/status')
def api_scheduler_status():
    """Get scheduler status"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'running': scheduler_running,
                'next_run': scraper_status_data['next_run'].strftime('%Y-%m-%d %H:%M:%S') if scraper_status_data['next_run'] else None,
                'total_runs': scraper_status_data['total_runs'],
                'successful_runs': scraper_status_data['successful_runs'],
                'failed_runs': scraper_status_data['failed_runs']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting scheduler status: {str(e)}'}), 500

if __name__ == '__main__':
    # Initialize the app before running
    initialize_app()
    app.run(debug=True, host='0.0.0.0', port=5001)
