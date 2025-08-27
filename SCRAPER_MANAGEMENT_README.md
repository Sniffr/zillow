# Scraper Management System

This document describes the new scraper management features added to the Zillow Property Manager.

## Overview

The scraper management system provides:
- **Automated scheduling** of scraper runs
- **Comprehensive logging** of all scraper executions
- **Real-time monitoring** of scraper and scheduler status
- **Configurable settings** stored in the database
- **Web dashboard** for managing and monitoring the scraper

## Features

### 1. Automated Scheduling
- Configure the scraper to run automatically at specified intervals
- Default: Every 10 minutes (configurable from 1 minute to 24 hours)
- Scheduler runs in the background when the Flask app starts
- Prevents multiple scraper instances from running simultaneously

### 2. Comprehensive Logging
- Every scraper execution is logged with a unique execution ID
- Logs include:
  - Start/end times
  - Execution status (running, completed, failed, cancelled)
  - Progress updates (searches processed, properties found/saved)
  - Error messages and details
  - Full log file content
- Logs are stored in both database and files
- Log files are saved in `static/logs/` directory

### 3. Real-time Monitoring
- Live status updates every 10 seconds
- Dashboard shows:
  - Scheduler status (running/stopped)
  - Scraper status (running/idle)
  - Next scheduled run time
  - Last run time
  - Current execution progress

### 4. Configurable Settings
All settings are stored in the database and can be modified through the web interface:

- **Enable/Disable Scheduler**: Turn automatic scheduling on/off
- **Schedule Interval**: How often to run the scraper (1-1440 minutes)
- **Timeout**: Maximum time to wait for scraper completion (1-120 minutes)
- **Max Concurrent Workers**: Number of simultaneous search processes (1-20)
- **Retry Attempts**: Number of retry attempts for failed operations (1-10)

### 5. Web Dashboard
Access the scraper management dashboard at `/scraper_management`:

- **Status Cards**: Real-time overview of system status
- **Configuration Tab**: Modify scraper settings
- **Logs Tab**: View execution history and download logs
- **Manual Controls**: Start scraper or scheduler manually

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Database Migration
```bash
python migrate_scraper_tables.py
```

### 3. Test the System
```bash
python test_scraper_system.py
```

### 4. Start the Application
```bash
python app.py
```

The scheduler will automatically start when the Flask app starts.

## Usage

### Starting the Scheduler
The scheduler starts automatically when you run `python app.py`. You can also:

- Start manually: Click "Start Scheduler" in the dashboard
- Stop manually: Click "Stop Scheduler" in the dashboard

### Running the Scraper
- **Automatically**: The scheduler will run the scraper based on your configuration
- **Manually**: Click "Start Scraper" in the dashboard
- **Command Line**: Run `python get_listing_and_agent.py` directly

### Monitoring Progress
1. Go to the Scraper Management dashboard
2. View real-time status in the status cards
3. Check the Logs tab for execution history
4. Click on any log entry to view detailed information
5. Download full log files for analysis

### Configuration
1. Go to the Configuration tab in the dashboard
2. Modify settings as needed
3. Click "Save Configuration"
4. Changes take effect immediately

## File Structure

```
zillow/
├── scraper_logger.py          # Logging utility
├── scraper_scheduler.py       # Scheduling system
├── migrate_scraper_tables.py  # Database migration
├── test_scraper_system.py     # Test script
├── static/
│   └── logs/                  # Log files directory
└── templates/
    └── scraper_management.html # Dashboard template
```

## Database Tables

### scraper_configs
Stores scraper configuration settings:
- `is_enabled`: Whether scheduling is enabled
- `schedule_interval_minutes`: How often to run
- `timeout_minutes`: Maximum execution time
- `max_concurrent_workers`: Number of workers
- `retry_attempts`: Retry count

### scraper_logs
Stores execution logs:
- `execution_id`: Unique identifier for each run
- `status`: Execution status
- `start_time`/`end_time`: Execution timing
- `total_searches`/`successful_searches`: Search results
- `total_properties`/`properties_saved`: Property results
- `error_message`/`error_details`: Error information
- `log_file_path`: Path to log file

## API Endpoints

### Scraper Configuration
- `GET /api/scraper_config` - Get current configuration
- `PUT /api/scraper_config` - Update configuration

### Scraper Logs
- `GET /api/scraper_logs` - Get recent logs
- `GET /api/scraper_logs/<execution_id>` - Get specific log details
- `GET /api/scraper_logs/<execution_id>/download` - Download log file

### Scraper Control
- `POST /api/scraper/start` - Start scraper manually
- `GET /api/scraper_status` - Get current status

### Scheduler Control
- `POST /api/scheduler/start` - Start scheduler
- `POST /api/scheduler/stop` - Stop scheduler

## Troubleshooting

### Common Issues

1. **Scheduler not starting**
   - Check if the `schedule` library is installed
   - Verify database connection
   - Check for Python errors in console

2. **Logs not appearing**
   - Ensure `static/logs/` directory exists
   - Check file permissions
   - Verify database migration completed

3. **Configuration not saving**
   - Check browser console for JavaScript errors
   - Verify API endpoints are accessible
   - Check database connection

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export FLASK_DEBUG=1
python app.py
```

### Manual Testing
Run the test script to verify all components:
```bash
python test_scraper_system.py
```

## Security Considerations

- Log files are stored in the `static/logs/` directory and may be accessible via web
- Consider implementing authentication for the scraper management dashboard
- Log files may contain sensitive information - implement proper access controls
- Database credentials should be properly secured

## Performance Notes

- The scheduler runs in a background thread and doesn't block the main application
- Log files are limited to last 100 lines in the web interface to prevent memory issues
- Old logs are automatically cleaned up (configurable retention period)
- Status updates are polled every 10 seconds to balance responsiveness and performance

## Future Enhancements

Potential improvements for future versions:
- Email notifications for failed runs
- More granular scheduling (specific times, days of week)
- Log rotation and compression
- Performance metrics and analytics
- Integration with external monitoring systems
- Webhook support for external integrations
