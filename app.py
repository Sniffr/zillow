"""
Flask web application for Zillow Property Manager
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database_models import DatabaseManager, Property, SearchConfig, MessageTemplate, ScraperConfig, ScraperLog
import subprocess
import threading
import os
import json
from datetime import datetime
import pandas as pd
from scraper_scheduler import get_scheduler, start_scheduler, stop_scheduler

app = Flask(__name__)
app.secret_key = 'zillow_property_manager_secret_key_2024'

# Global variable to track scraper status
scraper_status = {
    'running': False,
    'message': '',
    'last_run': None
}

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
                         scraper_status=scraper_status)

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

@app.route('/api/scraper_status')
def api_scraper_status():
    """Get current scraper status"""
    return jsonify(scraper_status)

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

# Scraper Management Routes
@app.route('/scraper_management')
def scraper_management():
    """Scraper management dashboard page"""
    return render_template('scraper_management.html')

@app.route('/api/scraper_config')
def api_get_scraper_config():
    """Get current scraper configuration"""
    try:
        db_manager = DatabaseManager()
        config = db_manager.get_scraper_config()
        
        config_data = {
            'id': config.id,
            'is_enabled': bool(config.is_enabled),
            'schedule_interval_minutes': config.schedule_interval_minutes,
            'last_scheduled_run': config.last_scheduled_run.isoformat() if config.last_scheduled_run else None,
            'next_scheduled_run': config.next_scheduled_run.isoformat() if config.next_scheduled_run else None,
            'max_concurrent_workers': config.max_concurrent_workers,
            'timeout_minutes': config.timeout_minutes,
            'retry_attempts': config.retry_attempts,
            'created_at': config.created_at.isoformat() if config.created_at else None,
            'updated_at': config.updated_at.isoformat() if config.updated_at else None
        }
        
        db_manager.close()
        return jsonify({'success': True, 'data': config_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting scraper configuration: {str(e)}'}), 500

@app.route('/api/scraper_config', methods=['PUT'])
def api_update_scraper_config():
    """Update scraper configuration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'schedule_interval_minutes' in data:
            interval = int(data['schedule_interval_minutes'])
            if interval < 1 or interval > 1440:  # Between 1 minute and 24 hours
                return jsonify({'success': False, 'message': 'Schedule interval must be between 1 and 1440 minutes'}), 400
        
        if 'timeout_minutes' in data:
            timeout = int(data['timeout_minutes'])
            if timeout < 1 or timeout > 120:  # Between 1 minute and 2 hours
                return jsonify({'success': False, 'message': 'Timeout must be between 1 and 120 minutes'}), 400
        
        # Update configuration
        scheduler = get_scheduler()
        success = scheduler.update_config(data)
        
        if success:
            return jsonify({'success': True, 'message': 'Scraper configuration updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update scraper configuration'}), 500
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating scraper configuration: {str(e)}'}), 500

@app.route('/api/scraper_logs')
def api_get_scraper_logs():
    """Get recent scraper logs"""
    try:
        db_manager = DatabaseManager()
        logs = db_manager.get_scraper_logs(limit=50)
        
        # Convert to list of dictionaries for DataTable
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'execution_id': log.execution_id,
                'status': log.status.title(),
                'start_time': log.start_time.strftime('%Y-%m-%d %H:%M:%S') if log.start_time else '',
                'end_time': log.end_time.strftime('%Y-%m-%d %H:%M:%S') if log.end_time else '',
                'total_searches': log.total_searches,
                'successful_searches': log.successful_searches,
                'total_properties': log.total_properties,
                'properties_saved': log.properties_saved,
                'error_message': log.error_message or '',
                'duration': _calculate_duration(log.start_time, log.end_time),
                'actions': f'''
                    <button class="btn btn-sm btn-info" onclick="viewScraperLog('{log.execution_id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="downloadScraperLog('{log.execution_id}')">
                        <i class="fas fa-download"></i>
                    </button>
                '''
            })
        
        db_manager.close()
        
        return jsonify({
            'data': data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting scraper logs: {str(e)}'}), 500

def _calculate_duration(start_time, end_time):
    """Calculate duration between start and end times"""
    if start_time and end_time:
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"
    elif start_time:
        return "Running..."
    return ""

@app.route('/api/scraper_logs/<execution_id>')
def api_get_scraper_log(execution_id):
    """Get specific scraper log details and content"""
    try:
        db_manager = DatabaseManager()
        log = db_manager.get_scraper_log_by_id(execution_id)
        
        if not log:
            db_manager.close()
            return jsonify({'success': False, 'message': 'Scraper log not found'}), 404
        
        # Get log file content if available
        log_content = []
        if log.log_file_path and os.path.exists(log.log_file_path):
            try:
                with open(log.log_file_path, 'r') as f:
                    log_content = f.readlines()
                    # Get last 100 lines
                    log_content = log_content[-100:] if len(log_content) > 100 else log_content
            except Exception as e:
                log_content = [f"Error reading log file: {str(e)}"]
        
        log_data = {
            'id': log.id,
            'execution_id': log.execution_id,
            'status': log.status,
            'start_time': log.start_time.isoformat() if log.start_time else None,
            'end_time': log.end_time.isoformat() if log.end_time else None,
            'total_searches': log.total_searches,
            'successful_searches': log.successful_searches,
            'total_properties': log.total_properties,
            'properties_saved': log.properties_saved,
            'error_message': log.error_message,
            'error_details': log.error_details,
            'log_file_path': log.log_file_path,
            'log_content': log_content,
            'created_at': log.created_at.isoformat() if log.created_at else None
        }
        
        db_manager.close()
        return jsonify({'success': True, 'data': log_data})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting scraper log: {str(e)}'}), 500

@app.route('/api/scraper_logs/<execution_id>/download')
def api_download_scraper_log(execution_id):
    """Download scraper log file"""
    try:
        db_manager = DatabaseManager()
        log = db_manager.get_scraper_log_by_id(execution_id)
        db_manager.close()
        
        if not log or not log.log_file_path or not os.path.exists(log.log_file_path):
            return jsonify({'success': False, 'message': 'Log file not found'}), 404
        
        # Return file path for download
        return jsonify({
            'success': True, 
            'file_path': log.log_file_path,
            'filename': f'scraper_log_{execution_id}.log'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error downloading log: {str(e)}'}), 500

@app.route('/api/scraper_status')
def api_get_scraper_status():
    """Get current scraper and scheduler status"""
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()
        
        # Add current scraper status
        status['scraper_running'] = scraper_status['running']
        status['scraper_message'] = scraper_status['message']
        status['scraper_last_run'] = scraper_status['last_run'].isoformat() if scraper_status['last_run'] else None
        
        return jsonify({'success': True, 'data': status})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting scraper status: {str(e)}'}), 500

@app.route('/api/scraper/start', methods=['POST'])
def api_start_scraper():
    """Start the scraper manually"""
    try:
        scheduler = get_scheduler()
        result = scheduler.run_now()
        
        if result['success']:
            # Update global scraper status
            global scraper_status
            scraper_status['running'] = True
            scraper_status['message'] = 'Scraper started manually'
            scraper_status['last_run'] = datetime.now()
            
            return jsonify({'success': True, 'message': result['message']})
        else:
            return jsonify({'success': False, 'message': result['message']}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting scraper: {str(e)}'}), 500

@app.route('/api/scheduler/start', methods=['POST'])
def api_start_scheduler():
    """Start the scraper scheduler"""
    try:
        start_scheduler()
        return jsonify({'success': True, 'message': 'Scheduler started successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting scheduler: {str(e)}'}), 500

@app.route('/api/scheduler/stop', methods=['POST'])
def api_stop_scheduler():
    """Stop the scraper scheduler"""
    try:
        stop_scheduler()
        return jsonify({'success': True, 'message': 'Scheduler stopped successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error stopping scheduler: {str(e)}'}), 500

if __name__ == '__main__':
    # Start the scraper scheduler
    try:
        start_scheduler()
        print("Scraper scheduler started successfully")
    except Exception as e:
        print(f"Warning: Could not start scraper scheduler: {str(e)}")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
