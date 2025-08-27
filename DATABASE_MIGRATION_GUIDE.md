# Database Migration Guide

## Overview
This guide documents the migration from JSON-based search configurations to a database-driven approach.

## Changes Made

### 1. New Database Table: `search_configs`
- **Purpose**: Stores search configuration parameters instead of using JSON files
- **Benefits**: 
  - Centralized configuration management
  - Ability to activate/deactivate searches
  - Better data integrity and validation
  - Easier to manage multiple search configurations

### 2. Database Schema
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

### 3. Updated Files
- `database_models.py` - Added `SearchConfig` model and database methods
- `get_listing_and_agent.py` - Updated to use database configs instead of JSON
- `migrate_configs_to_db.py` - Migration script to move JSON configs to database
- `manage_search_configs.py` - Management interface for search configurations

## Migration Process

### Step 1: Run Migration Script
```bash
python migrate_configs_to_db.py
```
This script will:
- Load existing configurations from `search_configs.json`
- Create new database records for each configuration
- Backup the original JSON file to `search_configs.json.backup`
- Display migration summary

### Step 2: Verify Migration
```bash
python test_database_configs.py
```
This script tests all database functionality to ensure everything works correctly.

### Step 3: Update Your Workflow
- **Before**: Edit `search_configs.json` manually
- **After**: Use the management script or database methods

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

### Programmatic Management
```python
from database_models import DatabaseManager

db_manager = DatabaseManager()

# Add new search configuration
config_data = {
    'search_value': 'Single family houses in San Diego',
    'ne_lat': 32.8,
    'ne_long': -117.0,
    'sw_lat': 32.7,
    'sw_long': -117.1,
    'pagination': 1,
    'description': 'San Diego area search'
}
db_manager.add_search_config(config_data)
db_manager.commit()

# Get active configurations
active_configs = db_manager.get_all_search_configs(active_only=True)

# Deactivate a configuration
db_manager.deactivate_search_config('Single family houses in San Diego')
```

## Benefits of the New System

1. **Centralized Management**: All configurations in one place
2. **Status Control**: Activate/deactivate searches without losing data
3. **Better Validation**: Database constraints ensure data integrity
4. **Audit Trail**: Track when configurations were created/modified
5. **Scalability**: Easier to manage large numbers of search configurations
6. **Integration**: Better integration with the existing property database

## Backward Compatibility

- The original JSON file is backed up during migration
- All existing search configurations are preserved
- The `get_listing_and_agent.py` script continues to work as before
- No changes needed to existing property data

## Troubleshooting

### Common Issues

1. **Migration fails**: Ensure the database is accessible and writable
2. **No configurations found**: Check if the migration script ran successfully
3. **Database errors**: Verify SQLite database file permissions

### Recovery

If you need to restore the JSON-based approach:
1. Restore `search_configs.json.backup` to `search_configs.json`
2. Revert changes in `get_listing_and_agent.py`
3. Remove the `SearchConfig` model from `database_models.py`

## Future Enhancements

- Web interface for managing search configurations
- Bulk import/export of configurations
- Configuration templates for common search patterns
- Integration with property search results for better analytics
