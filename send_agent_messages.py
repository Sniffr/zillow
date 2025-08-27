import pandas as pd
import os
from database_models import DatabaseManager, Property
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import json
import re

def load_twilio_config(config_file='twilio_config.json'):
    """
    Load Twilio configuration from JSON file
    
    Args:
        config_file (str): Path to configuration file
        
    Returns:
        dict: Twilio configuration or None if failed
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config.get('twilio')
    except FileNotFoundError:
        print(f"Configuration file '{config_file}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Invalid JSON format in '{config_file}'.")
        return None

def load_properties_from_database(db_manager):
    """
    Load all properties from the database
    
    Args:
        db_manager: DatabaseManager instance
        
    Returns:
        dict: Dictionary with search_term as key and list of properties as value
    """
    properties_by_search = {}
    
    # Get all unique search terms
    search_terms = db_manager.get_unique_search_terms()
    
    if not search_terms:
        print("No properties found in the database.")
        return properties_by_search
    
    print(f"Found {len(search_terms)} search terms in database:")
    
    for search_term in search_terms:
        properties = db_manager.get_properties_by_search_term(search_term)
        properties_by_search[search_term] = properties
        print(f"  • {search_term}: {len(properties)} properties")
    
    return properties_by_search

def extract_phone_numbers_from_properties(properties):
    """
    Extract phone numbers from property objects
    
    Args:
        properties: List of Property objects
        
    Returns:
        dict: Dictionary with agent names as keys and phone numbers as values
    """
    agent_phones = {}
    
    for prop in properties:
        # Check for agent phone number
        if prop.attribution_agent_phone_number:
            phone = str(prop.attribution_agent_phone_number).strip()
            agent_name = prop.attribution_agent_name or "Unknown Agent"
            
            if phone and phone not in ['None', 'null', '']:
                # Clean the phone number (remove non-digit characters)
                cleaned_phone = re.sub(r'[^\d]', '', phone)
                
                # Ensure it's a valid US phone number (10 or 11 digits)
                if len(cleaned_phone) == 10:
                    # Add +1 for US numbers
                    cleaned_phone = "+1" + cleaned_phone
                elif len(cleaned_phone) == 11 and cleaned_phone.startswith('1'):
                    cleaned_phone = "+" + cleaned_phone
                elif len(cleaned_phone) == 11 and not cleaned_phone.startswith('+'):
                    cleaned_phone = "+" + cleaned_phone
                else:
                    print(f"    Skipping invalid phone number for {agent_name}: {phone}")
                    continue
                
                agent_phones[agent_name] = {
                    'phone': cleaned_phone,
                    'address': prop.address,
                    'price': prop.price,
                    'search_term': prop.search_term
                }
        
        # Also check for broker phone number if different
        if prop.attribution_broker_phone_number:
            phone = str(prop.attribution_broker_phone_number).strip()
            broker_name = prop.attribution_broker_name or "Unknown Broker"
            
            if phone and phone not in ['None', 'null', '']:
                cleaned_phone = re.sub(r'[^\d]', '', phone)
                
                if len(cleaned_phone) == 10:
                    cleaned_phone = "+1" + cleaned_phone
                elif len(cleaned_phone) == 11 and cleaned_phone.startswith('1'):
                    cleaned_phone = "+" + cleaned_phone
                elif len(cleaned_phone) == 11 and not cleaned_phone.startswith('+'):
                    cleaned_phone = "+" + cleaned_phone
                else:
                    continue
                
                # Only add if it's a different number
                if broker_name not in agent_phones or agent_phones[broker_name]['phone'] != cleaned_phone:
                    agent_phones[f"{broker_name} (Broker)"] = {
                        'phone': cleaned_phone,
                        'address': prop.address,
                        'price': prop.price,
                        'search_term': prop.search_term
                    }
        
        # Check for co-agent phone number
        if prop.attribution_co_agent_number:
            phone = str(prop.attribution_co_agent_number).strip()
            co_agent_name = prop.attribution_co_agent_name or "Unknown Co-Agent"
            
            if phone and phone not in ['None', 'null', '']:
                cleaned_phone = re.sub(r'[^\d]', '', phone)
                
                if len(cleaned_phone) == 10:
                    cleaned_phone = "+1" + cleaned_phone
                elif len(cleaned_phone) == 11 and cleaned_phone.startswith('1'):
                    cleaned_phone = "+" + cleaned_phone
                elif len(cleaned_phone) == 11 and not cleaned_phone.startswith('+'):
                    cleaned_phone = "+" + cleaned_phone
                else:
                    continue
                
                if co_agent_name not in agent_phones or agent_phones[co_agent_name]['phone'] != cleaned_phone:
                    agent_phones[f"{co_agent_name} (Co-Agent)"] = {
                        'phone': cleaned_phone,
                        'address': prop.address,
                        'price': prop.price,
                        'search_term': prop.search_term
                    }
    
    return agent_phones

def send_twilio_message(phone_number, message, twilio_client, from_phone):
    """
    Send a text message using Twilio
    
    Args:
        phone_number (str): Recipient phone number
        message (str): Message to send
        twilio_client: Twilio client instance
        from_phone (str): Twilio phone number to send from
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Send the message
        message_obj = twilio_client.messages.create(
            body=message,
            from_=from_phone,
            to=phone_number
        )
        
        print(f"    Message sent successfully. SID: {message_obj.sid}")
        return True
        
    except TwilioException as e:
        print(f"    Twilio error: {str(e)}")
        return False
    except Exception as e:
        print(f"    Unexpected error: {str(e)}")
        return False

def send_messages_to_agents(properties_by_search, message_template, twilio_client, from_phone):
    """
    Send messages to all agent phone numbers found in database
    
    Args:
        properties_by_search (dict): Dictionary of search terms and their properties
        message_template (str): Message template to send to agents
        twilio_client: Twilio client instance
        from_phone (str): Twilio phone number to send from
        
    Returns:
        dict: Summary of results
    """
    results = {
        'total_search_terms': len(properties_by_search),
        'total_agents': 0,
        'successful_sends': 0,
        'failed_sends': 0,
        'agents_contacted': []
    }
    
    all_agents = {}
    
    # Process each search term
    for search_term, properties in properties_by_search.items():
        print(f"\nProcessing '{search_term}'...")
        
        # Extract phone numbers from properties
        agent_phones = extract_phone_numbers_from_properties(properties)
        
        if not agent_phones:
            print(f"  No valid phone numbers found for '{search_term}'")
            continue
        
        print(f"  Found {len(agent_phones)} unique agents/brokers with phone numbers")
        
        # Merge with all_agents to avoid duplicate messages
        for agent_name, agent_info in agent_phones.items():
            if agent_info['phone'] not in [a['phone'] for a in all_agents.values()]:
                all_agents[agent_name] = agent_info
    
    results['total_agents'] = len(all_agents)
    
    # Send messages to each unique agent
    print(f"\n{'='*60}")
    print(f"Sending messages to {len(all_agents)} unique agents...")
    print(f"{'='*60}")
    
    for agent_name, agent_info in all_agents.items():
        print(f"\n  Agent: {agent_name}")
        print(f"  Phone: {agent_info['phone']}")
        print(f"  Property: {agent_info['address']}")
        print(f"  Price: {agent_info['price']}")
        
        # Customize message with property details
        message = message_template.format(
            agent_name=agent_name.split(' (')[0],  # Remove (Broker) or (Co-Agent) suffix
            property_address=agent_info['address'],
            property_price=agent_info['price'],
            search_area=agent_info['search_term']
        )
        
        if send_twilio_message(agent_info['phone'], message, twilio_client, from_phone):
            results['successful_sends'] += 1
            results['agents_contacted'].append({
                'name': agent_name,
                'phone': agent_info['phone'],
                'property': agent_info['address']
            })
        else:
            results['failed_sends'] += 1
    
    return results

def main():
    """
    Main function to load properties from database and send messages
    """
    # Initialize database connection
    print("Connecting to database...")
    db_manager = DatabaseManager()
    print("Connected to zillow_properties.db")
    
    # Load properties from database
    print("\nLoading properties from database...")
    properties_by_search = load_properties_from_database(db_manager)
    
    if not properties_by_search:
        print("No properties found in database. Exiting.")
        db_manager.close()
        return
    
    # Count total properties
    total_properties = sum(len(props) for props in properties_by_search.values())
    print(f"\nTotal properties in database: {total_properties}")
    
    # Initialize Twilio client
    twilio_client = None
    from_phone = None
    
    # Try to get credentials from environment variables first
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_phone = os.getenv('TWILIO_PHONE_NUMBER')
    
    # If not in environment, try config file
    if not all([account_sid, auth_token, from_phone]):
        print("\nTwilio credentials not found in environment variables.")
        print("Trying to load from config file...")
        
        config = load_twilio_config()
        if config:
            account_sid = config.get('account_sid')
            auth_token = config.get('auth_token')
            from_phone = config.get('phone_number')
    
    # Check if we have all required credentials
    if not all([account_sid, auth_token, from_phone]):
        print("\nTwilio credentials not found. Please set environment variables or update twilio_config.json")
        print("Required: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER")
        db_manager.close()
        return
    
    try:
        twilio_client = Client(account_sid, auth_token)
        print("\nTwilio client initialized successfully")
        print(f"Using phone number: {from_phone}")
        
    except Exception as e:
        print(f"\nError initializing Twilio client: {str(e)}")
        db_manager.close()
        return
    
    # Load message template from config or use default
    config = load_twilio_config()
    if config and 'message' in config:
        message_template = config['message'].get('template', None)
        if not message_template:
            message_template = config['message'].get('default_text', 
                "Hello {agent_name}! I'm interested in the property at {property_address} listed at {property_price}. Could you please send me more information? Thank you!")
    else:
        message_template = """Hello {agent_name}! 

I saw your listing for the property at {property_address} (listed at {property_price}) in the {search_area} area.

I'm very interested in learning more about this property. Could you please send me additional information and let me know when we could schedule a viewing?

Thank you!"""
    
    # Send messages to agents
    print(f"\n{'='*60}")
    print("STARTING MESSAGE CAMPAIGN")
    print(f"{'='*60}")
    
    results = send_messages_to_agents(properties_by_search, message_template, twilio_client, from_phone)
    
    # Print summary
    print(f"\n{'='*60}")
    print("MESSAGE SENDING SUMMARY")
    print(f"{'='*60}")
    print(f"Total search terms processed: {results['total_search_terms']}")
    print(f"Total unique agents found: {results['total_agents']}")
    print(f"Successful sends: {results['successful_sends']}")
    print(f"Failed sends: {results['failed_sends']}")
    
    if results['agents_contacted']:
        print(f"\nAgents successfully contacted:")
        for agent in results['agents_contacted']:
            print(f"  ✓ {agent['name']} - {agent['phone']}")
            print(f"    Property: {agent['property']}")
    
    # Close database connection
    db_manager.close()
    print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()