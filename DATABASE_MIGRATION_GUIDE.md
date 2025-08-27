# Database Migration Guide

## Overview
This guide documents the migration from JSON-based search configurations and hardcoded message templates to a database-driven approach.

## Changes Made

### 1. New Database Table: `search_configs`
- **Purpose**: Stores search configuration parameters instead of using JSON files
- **Benefits**: 
  - Centralized configuration management
  - Ability to activate/deactivate searches
  - Better data integrity and validation
  - Easier to manage multiple search configurations

### 2. New Database Table: `message_templates`
- **Purpose**: Stores message templates instead of hardcoded values
- **Benefits**:
  - Centralized template management
  - Multiple template support with categories
  - Default template system
  - Template versioning and status control
  - Variable tracking for templates

### 3. Database Schema

#### Search Configs Table
```sql
CREATE TABLE search_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_value VARCHAR(500) NOT NULL UNIQUE,
    ne_lat FLOAT NOT NULL,
    ne_long FLOAT NOT NULL,
    sw_lat FLOAT NOT NULL,
    sw_long FLOAT NOT NULL,
    pagination INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Message Templates Table
```sql
CREATE TABLE message_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    template_text TEXT NOT NULL,
    is_default INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    description TEXT,
    category VARCHAR(100) DEFAULT 'general',
    available_variables TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4. Updated Files
- `database_models.py` - Added `SearchConfig` and `MessageTemplate` models with database methods
- `get_listing_and_agent.py` - Updated to use database configs instead of JSON
- `send_agent_messages.py` - Updated to use database templates instead of hardcoded ones
- `migrate_configs_to_db.py` - Migration script for search configurations
- `migrate_message_templates_to_db.py` - Migration script for message templates
- `manage_search_configs.py` - Management interface for search configurations
- `manage_message_templates.py` - Management interface for message templates

## Migration Process

### Step 1: Run Search Configuration Migration
```bash
python migrate_configs_to_db.py
```
This script will:
- Load existing configurations from `search_configs.json`
- Create new database records for each configuration
- Backup the original JSON file to `search_configs.json.backup`
- Display migration summary

### Step 2: Run Message Template Migration
```bash
python migrate_message_templates_to_db.py
```
This script will:
- Load existing templates from `twilio_config.json`
- Create new database records for each template
- Set the main template as default
- Backup the original config to `twilio_config.json.backup`
- Display migration summary

### Step 3: Verify Migration
```bash
python manage_search_configs.py
python manage_message_templates.py
```
Use these management scripts to verify that all configurations and templates were migrated correctly.

## Managing Search Configurations

### Using the Management Script
```bash
python manage_search_configs.py
```

**Available Options:**
1. **View all configurations** - See all search configurations and their status
2. **Add new configuration** - Interactive form to add new search areas
3. **Toggle status** - Activate/deactivate configurations without deleting
4. **Delete configuration** - Permanently remove configurations

## Managing Message Templates

### Using the Management Script
```bash
python manage_message_templates.py
```

**Available Options:**
1. **View all templates** - See all message templates and their status
2. **View template text** - View the full text of a specific template
3. **Add new template** - Interactive form to add new message templates
4. **Set default template** - Choose which template to use by default
5. **Toggle status** - Activate/deactivate templates without deleting
6. **Delete template** - Permanently remove templates (cannot delete default)

### Programmatic Management
```python
from database_models import DatabaseManager

db_manager = DatabaseManager()

# Add new message template
template_data = {
    'name': 'Follow-up Template',
    'template_text': 'Hi {agent_name}, following up on the property at {property_address}...',
    'description': 'Template for follow-up messages',
    'category': 'follow_up',
    'available_variables': json.dumps(['agent_name', 'property_address']),
    'is_default': False,
    'is_active': True
}
db_manager.add_message_template(template_data)
db_manager.commit()

# Get default template
default_template = db_manager.get_default_message_template()

# Set a different template as default
db_manager.set_default_message_template('Follow-up Template')
```

## Template Variables

The system supports these standard variables in message templates:
- `{agent_name}` - Name of the real estate agent
- `{property_address}` - Address of the property
- `{property_price}` - Price of the property
- `{search_area}` - Search area/term used

## Benefits of the New System

1. **Centralized Management**: All configurations and templates in one place
2. **Status Control**: Activate/deactivate searches and templates without losing data
3. **Better Validation**: Database constraints ensure data integrity
4. **Audit Trail**: Track when configurations and templates were created/modified
5. **Scalability**: Easier to manage large numbers of configurations and templates
6. **Integration**: Better integration with the existing property database
7. **Template System**: Multiple message templates with categories and default selection
8. **Variable Tracking**: Automatic detection and tracking of template variables

## Backward Compatibility

- The original JSON files are backed up during migration
- All existing search configurations and message templates are preserved
- The `get_listing_and_agent.py` script continues to work as before
- The `send_agent_messages.py` script now uses database templates with fallback
- No changes needed to existing property data

## Troubleshooting

### Common Issues

1. **Migration fails**: Ensure the database is accessible and writable
2. **No configurations/templates found**: Check if the migration scripts ran successfully
3. **Database errors**: Verify SQLite database file permissions
4. **Template not found**: Ensure there's a default template set in the database

### Recovery

If you need to restore the JSON-based approach:
1. Restore backup files (e.g., `search_configs.json.backup`, `twilio_config.json.backup`)
2. Revert changes in the respective Python files
3. Remove the new models from `database_models.py`

## Future Enhancements

- Web interface for managing configurations and templates
- Bulk import/export of configurations and templates
- Template versioning and rollback
- Advanced template editor with variable validation
- Integration with property search results for better analytics
- Template performance tracking and A/B testing
