# Zillow Property Manager

A comprehensive web application for scraping, managing, and analyzing Zillow property listings with agent contact information and automated messaging capabilities.

## 🏠 What This Application Does

The Zillow Property Manager is a Flask-based web application that:

- **Scrapes Zillow listings** using the pyzill library to collect property data and agent information
- **Stores data** in a SQLite database with comprehensive property and attribution details
- **Provides a web dashboard** for viewing, managing, and analyzing property data
- **Automates messaging** to agents via Twilio SMS integration
- **Exports data** to CSV format for further analysis
- **Manages search configurations** for different geographic areas and search terms
- **Implements retry mechanisms** and concurrent processing for robust scraping
- **Handles proxy support** for reliable data collection

## ✨ Key Features

- **Property Dashboard**: View statistics, run scrapers, and manage properties
- **DataTable Interface**: Browse all properties with search, sort, and filter capabilities
- **Property Details**: View comprehensive property information and agent attribution data
- **Automated Scraping**: Run property scrapers with real-time status updates and retry logic
- **Agent Messaging**: Send automated SMS messages to property agents via Twilio
- **Data Export**: Export property data to CSV format
- **Search Configuration Management**: Configure and manage different search areas with geographic coordinates
- **Concurrent Processing**: Multi-threaded property processing for improved performance
- **Error Handling**: Robust error handling with retry mechanisms and logging

## 🏗️ Architecture & File Structure

```
zillow/
├── app.py                          # Main Flask application with web interface
├── database_models.py              # SQLAlchemy database models and management
├── get_listing_and_agent.py       # Zillow scraping logic with retry mechanisms
├── send_agent_messages.py         # Twilio SMS messaging system
├── manage_search_configs.py       # CLI tool for search configuration management
├── requirements.txt                # Python dependencies
├── twilio_config.json             # Twilio API configuration
├── zillow_properties.db           # SQLite database
├── config.py                      # Configuration management for different environments
├── Dockerfile                     # Docker image definition
├── docker-compose.yml             # Docker Compose orchestration
├── docker-entrypoint.sh           # Docker container initialization script
├── docker-setup.sh                # Automated Docker setup script
├── .dockerignore                  # Docker build exclusions
├── DOCKER_README.md               # Docker deployment documentation
├── static/                        # Static assets
│   ├── css/style.css             # Custom styles and Bootstrap integration
│   ├── js/main.js                # JavaScript functionality and AJAX calls
│   └── exports/                  # CSV export directory
└── templates/                     # HTML templates
    ├── base.html                 # Base template with navigation and Bootstrap
    ├── index.html                # Dashboard page with statistics and controls
    ├── properties.html           # Properties listing page with DataTable
    └── property_detail.html      # Individual property view with attribution data
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip package manager
- Twilio account (for SMS messaging features)
- Internet connection for Zillow scraping

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd zillow
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Twilio** (optional, for SMS features)
   - Copy `twilio_config.json.example` to `twilio_config.json`
   - Add your Twilio credentials:
     ```json
     {
       "twilio": {
         "account_sid": "your_account_sid",
         "auth_token": "your_auth_token",
         "phone_number": "your_twilio_phone_number"
       }
     }
     ```

### Running the Application

#### Option 1: Traditional Installation
1. **Start the web application**
   ```bash
   python app.py
   ```
   The app will be available at `http://localhost:5001`

#### Option 2: Docker Deployment (Recommended)
1. **Quick setup with Docker**
   ```bash
   ./docker-setup.sh
   ```
   This script will automatically set up and start the application using Docker.

2. **Manual Docker setup**
   ```bash
   # Build and start with Docker Compose
   docker-compose up --build -d
   
   # Access the application
   open http://localhost:5001
   ```

   For detailed Docker instructions, see [DOCKER_README.md](DOCKER_README.md).

2. **Access the dashboard**
   - Open your browser and navigate to `http://localhost:5001`
   - View property statistics and run scrapers
   - Browse properties and manage data

## 📊 Database Schema

### Properties Table
- **Basic Info**: ID, search_term, address, price, sold_by, URL
- **Geographic Coordinates**: ne_lat, ne_long, sw_lat, sw_long (search boundaries)
- **Comprehensive Attribution Data**:
  - Agent information: name, email, phone, license number
  - Broker information: name, phone number
  - Co-agent details: name, phone, license
  - MLS information: ID, name, disclaimer, listing agreement
  - Additional attribution fields for flexibility
- **Timestamps**: created_at, updated_at
- **Flexible Storage**: JSON field for additional attribution data

### Search Configs Table
- **Search Parameters**: search_value, geographic boundaries, pagination
- **Metadata**: is_active status, description, timestamps
- **Coordinates**: Northeast and Southwest boundaries for geographic searches

## 🔧 Core Components

### 1. Web Application (`app.py`)
- **Flask Web Server**: Dashboard, properties view, and API endpoints
- **Real-time Monitoring**: Scraper status with live updates
- **Data Export**: CSV export functionality with timestamped filenames
- **Property Management**: View, search, and manage property listings
- **Toast Notifications**: User-friendly feedback using Bootstrap toasts

### 2. Data Scraping (`get_listing_and_agent.py`)
- **Pyzill Integration**: Uses pyzill library for Zillow data extraction
- **Retry Mechanisms**: Configurable retry logic with exponential backoff
- **Concurrent Processing**: Multi-threaded property processing for performance
- **Proxy Support**: Optional proxy configuration for reliable scraping
- **Error Handling**: Comprehensive error handling and logging
- **Database Integration**: Direct database saving with duplicate prevention

### 3. Messaging System (`send_agent_messages.py`)
- **Twilio Integration**: SMS messaging via Twilio API
- **Phone Number Extraction**: Automatic extraction from property attribution data
- **Number Validation**: US phone number formatting and validation
- **Message Templates**: Configurable message content
- **Batch Processing**: Process multiple properties and agents efficiently

### 4. Database Management (`database_models.py`)
- **SQLAlchemy ORM**: Modern database interface with models
- **Connection Management**: Efficient database connection handling
- **CRUD Operations**: Complete database operations for properties and configs
- **Data Validation**: Input validation and error handling
- **Flexible Schema**: JSON fields for extensible attribution data

### 5. Search Configuration (`manage_search_configs.py`)
- **CLI Interface**: Command-line tool for managing search configurations
- **Geographic Setup**: Coordinate-based search area configuration
- **Active/Inactive Management**: Toggle search configurations on/off
- **Validation**: Input validation for coordinates and search parameters

## 🎯 Usage Workflow

### 1. **Setup Search Areas**
   ```bash
   python manage_search_configs.py
   ```
   - Add new search configurations with geographic coordinates
   - Define search terms and boundaries
   - Set pagination and descriptions

### 2. **Run Property Scraper**
   - Use the web dashboard to start scraping
   - Monitor real-time progress and status
   - View completion messages and error logs

### 3. **Review and Analyze Data**
   - Browse properties through the web interface
   - View detailed property information and agent data
   - Use DataTable features for sorting and filtering

### 4. **Send Agent Messages**
   - Extract phone numbers from property data
   - Send automated SMS messages via Twilio
   - Monitor message delivery and responses

### 5. **Export and Analyze**
   - Download CSV exports for external analysis
   - Use data for lead generation and market research
   - Track property trends and agent information

## 🔒 Security & Configuration

- **Flask Security**: Secret key configuration in `app.py`
- **Twilio Credentials**: Stored in separate configuration file
- **Database Security**: SQLite file permissions and access control
- **Environment Variables**: Recommended for production deployments
- **Proxy Configuration**: Optional proxy support for scraping

## 🧪 Testing & Development

- **Database Testing**: Test database connections and models
- **Scraping Validation**: Verify data extraction and processing
- **Message Testing**: Test Twilio integration with test numbers
- **Error Handling**: Test retry mechanisms and error scenarios

## 📝 API Endpoints

### Web Interface
- `GET /`: Dashboard with statistics and controls
- `GET /properties`: Properties listing with DataTable
- `GET /property/<id>`: Individual property details
- `GET /toast_demo`: Toast notification demonstration

### API Endpoints
- `GET /api/properties`: JSON data for DataTable
- `POST /run_scraper`: Execute property scraper
- `POST /send_messages`: Send agent messages
- `GET /export_csv`: Export data to CSV
- `GET /api/scraper_status`: Current scraper status

## 🚨 Troubleshooting

### Common Issues

1. **Scraper Fails**
   - Check internet connection and Zillow access
   - Verify search configurations are active
   - Check console logs for detailed error messages

2. **Database Errors**
   - Ensure SQLite file has write permissions
   - Check database connection in console output
   - Verify database schema is properly initialized

3. **Twilio Integration Issues**
   - Verify credentials in `twilio_config.json`
   - Check Twilio account status and phone number
   - Test with a known working phone number

4. **Import/Module Errors**
   - Ensure all dependencies are installed
   - Check Python version compatibility
   - Verify virtual environment is activated

### Performance Optimization

- **Concurrent Processing**: Adjust thread pool size in scraping
- **Database Indexing**: Ensure proper database indexes for large datasets
- **Memory Management**: Monitor memory usage during large scraping operations
- **Proxy Rotation**: Use multiple proxies for high-volume scraping

## 🔄 Advanced Features

### Retry Mechanisms
- **Configurable Retries**: Set retry attempts for different operations
- **Exponential Backoff**: Intelligent retry timing with backoff factors
- **Error Classification**: Different retry strategies for different error types

### Concurrent Processing
- **Thread Pool**: Configurable thread pool for property processing
- **Resource Management**: Efficient resource utilization during scraping
- **Progress Tracking**: Real-time progress updates and status monitoring

### Data Validation
- **Phone Number Formatting**: Automatic US phone number formatting
- **Coordinate Validation**: Geographic boundary validation
- **Data Integrity**: Duplicate prevention and data consistency checks

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly** with different scenarios
5. **Submit a pull request** with detailed description

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support & Maintenance

### Regular Maintenance
- **Database Cleanup**: Regular cleanup of old or duplicate data
- **Log Rotation**: Manage log files and console output
- **Performance Monitoring**: Track scraping performance and database usage

### Getting Help
- **Check Logs**: Review console output and error messages
- **Verify Configuration**: Ensure all configuration files are correct
- **Test Components**: Test individual components in isolation
- **Community Support**: Check GitHub issues and discussions

## 🚀 Future Enhancements

- **Real-time Notifications**: WebSocket support for live updates
- **Advanced Analytics**: Property market analysis and trends
- **Multi-platform Support**: Mobile app and API endpoints
- **Enhanced Messaging**: Email integration and message templates
- **Data Visualization**: Charts and graphs for property data
- **Automated Scheduling**: Cron jobs for regular scraping

