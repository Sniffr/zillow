"""
Flask web application for Zillow Property Manager
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from database_models import DatabaseManager, Property
import subprocess
import threading
import os
import json
from datetime import datetime
import pandas as pd

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
