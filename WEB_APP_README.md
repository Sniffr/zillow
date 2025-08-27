# Zillow Property Manager - Web Application

A modern, responsive web application built with Flask for managing Zillow property listings, running scrapers, and sending messages to agents.

## Features

### 🏠 **Dashboard**
- Real-time statistics showing total properties, search terms, and contact information
- Quick action buttons for running scrapers and sending messages
- Live status updates for scraper operations

### 📊 **DataTables Integration**
- Responsive, searchable property listings
- Advanced filtering by search terms
- Sortable columns with pagination
- Export functionality to CSV

### 🤖 **Automated Operations**
- One-click scraper execution from the web interface
- Background processing with real-time status updates
- Bulk messaging to agents and brokers
- Automatic data refresh

### 📱 **Responsive Design**
- Mobile-friendly interface using Bootstrap 5
- DataTables responsive mode for small screens
- Touch-friendly buttons and controls

### 🔔 **Toast Notifications**
- Modern toast notifications instead of JavaScript alerts
- Different types: success, error, warning, info
- Auto-dismiss with customizable duration
- Responsive design for mobile devices

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Database Setup
The application uses SQLite by default. The database will be created automatically when you first run the scraper.

### 3. Configuration
Ensure your configuration files are set up:
- `search_configs.json` - Search areas and parameters
- `twilio_config.json` - Twilio credentials for messaging

### 4. Run the Web Application
```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## Usage

### Dashboard
- **Statistics Cards**: View total properties, search terms, and contact information
- **Run Scraper**: Click to start the Zillow property scraper
- **Send Messages**: Send bulk messages to all agents in the database
- **Quick Actions**: Access properties, export data, and refresh statistics

### Properties Page
- **DataTable**: View all properties in a searchable, sortable table
- **Filters**: Filter by search terms using the dropdown
- **Actions**: View property details or send individual messages
- **Export**: Download all data as CSV

### Property Details
- **Basic Info**: Price, status, search term, and creation date
- **Contact Information**: Agent, broker, and co-agent details
- **MLS Information**: MLS name, ID, and disclaimers
- **Additional Data**: All attribution fields from Zillow

## File Structure

```
zillow/
├── app.py                          # Flask application
├── templates/                      # HTML templates
│   ├── base.html                   # Base template with navigation
│   ├── index.html                  # Dashboard page
│   ├── properties.html             # Properties listing page
│   ├── property_detail.html        # Property detail modal
│   └── toast_demo.html             # Toast notification demo page
├── static/                         # Static files
│   ├── css/
│   │   └── style.css              # Custom styles
│   ├── js/
│   │   └── main.js                # JavaScript utilities
│   └── exports/                   # CSV export directory
├── database_models.py              # Database models
├── get_listing_and_agent.py        # Property scraper
├── send_agent_messages.py          # Messaging system
└── requirements.txt                # Python dependencies
```

## API Endpoints

### Dashboard
- `GET /` - Main dashboard with statistics
- `POST /run_scraper` - Start the property scraper
- `POST /send_messages` - Send messages to agents
- `GET /api/scraper_status` - Get scraper status

### Properties
- `GET /properties` - Properties page with DataTable
- `GET /api/properties` - JSON data for DataTable
- `GET /property/<id>` - Property detail view
- `GET /export_csv` - Export properties to CSV

### Demo & Utilities
- `GET /toast_demo` - Toast notification demo page

## Configuration

### Twilio Setup
1. Create a `twilio_config.json` file:
```json
{
    "twilio": {
        "account_sid": "YOUR_ACCOUNT_SID",
        "auth_token": "YOUR_AUTH_TOKEN",
        "phone_number": "+1234567890"
    },
    "message": {
        "template": "Hello {agent_name}! I saw your listing for the property at {property_address} (listed at {property_price}) in the {search_area} area. I'm very interested in learning more about this property. Could you please send me additional information and let me know when we could schedule a viewing? Thank you!"
    }
}
```

### Search Configuration
Update `search_configs.json` with your desired search areas:
```json
[
    {
        "search_value": "Single family houses in Los Angeles",
        "ne_lat": 34.05,
        "ne_long": -118.24,
        "sw_lat": 33.70,
        "sw_long": -118.67,
        "pagination": 1
    }
]
```

## Features in Detail

### Real-time Scraper Control
- Start/stop scraper from web interface
- Live status updates with progress messages
- Background processing with threading
- Automatic page refresh when complete

### Advanced DataTable Features
- Server-side processing for large datasets
- Responsive design for mobile devices
- Custom filters and search functionality
- Export to CSV with timestamp

### Messaging System
- Bulk messaging to all agents
- Personalized messages with property details
- Phone number validation and formatting
- Success/failure tracking

### Responsive Design
- Bootstrap 5 for modern UI components
- Mobile-first responsive design
- Touch-friendly interface
- Optimized for all screen sizes

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure SQLite is working properly
   - Check file permissions for database creation

2. **Scraper Not Starting**
   - Verify all dependencies are installed
   - Check proxy configuration in scraper script
   - Ensure search_configs.json is valid

3. **Messages Not Sending**
   - Verify Twilio credentials in twilio_config.json
   - Check phone number format (+1XXXXXXXXXX)
   - Ensure Twilio account has sufficient credits

4. **Web App Not Loading**
   - Check if port 5000 is available
   - Verify Flask is installed: `pip install flask`
   - Check console for error messages

### Debug Mode
Run the application in debug mode for detailed error messages:
```bash
export FLASK_ENV=development
python app.py
```

## Security Considerations

- Change the default secret key in `app.py`
- Use environment variables for sensitive data
- Implement user authentication for production use
- Add rate limiting for API endpoints
- Use HTTPS in production

## Production Deployment

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker
Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review the console logs for error messages
- Ensure all dependencies are properly installed
- Verify configuration files are correctly formatted
