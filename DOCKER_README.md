# Docker Deployment Guide for Zillow Property Manager

This guide explains how to deploy the Zillow Property Manager application using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system
- Git (to clone the repository)

## Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd zillow
   ```

2. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   Open your browser and navigate to `http://localhost:5001`

## Docker Configuration

### Files Created

- `Dockerfile` - Defines the Docker image
- `docker-compose.yml` - Orchestrates the application services
- `.dockerignore` - Excludes unnecessary files from the build context
- `config.py` - Configuration management for different environments
- `docker-entrypoint.sh` - Initialization script for the container

### Volume Mounts

The following directories are mounted as volumes for data persistence:

- `./data` → `/app/data` (Database files)
- `./logs` → `/app/logs` (Application logs)
- `./csv_exports` → `/app/csv_exports` (CSV export files)
- `./static/exports` → `/app/static/exports` (Static export files)
- `./static/logs` → `/app/static/logs` (Static log files)

### Configuration Files

The following configuration files are mounted as read-only:
- `twilio_config.json` → `/app/twilio_config.json`
- `scraper_schedule.json` → `/app/scraper_schedule.json`

## Environment Variables

You can customize the application behavior by setting environment variables:

```bash
# Database configuration
DATABASE_URL=sqlite:///data/zillow_properties.db

# Flask configuration
FLASK_ENV=production
DEBUG=false
SECRET_KEY=your-secret-key-here

# Application settings
HOST=0.0.0.0
PORT=5001

# File paths
LOG_DIR=/app/logs
CSV_EXPORT_DIR=/app/csv_exports
STATIC_EXPORT_DIR=/app/static/exports
STATIC_LOG_DIR=/app/static/logs

# Configuration files
TWILIO_CONFIG_FILE=twilio_config.json
SCRAPER_SCHEDULE_FILE=scraper_schedule.json
```

## Docker Commands

### Build the image
```bash
docker build -t zillow-property-manager .
```

### Run the container
```bash
docker run -d \
  --name zillow-app \
  -p 5001:5001 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/csv_exports:/app/csv_exports \
  -v $(pwd)/static/exports:/app/static/exports \
  -v $(pwd)/static/logs:/app/static/logs \
  -v $(pwd)/twilio_config.json:/app/twilio_config.json:ro \
  -v $(pwd)/scraper_schedule.json:/app/scraper_schedule.json:ro \
  zillow-property-manager
```

### Using Docker Compose

**Start the application:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Stop the application:**
```bash
docker-compose down
```

**Rebuild and restart:**
```bash
docker-compose up --build -d
```

## Data Persistence

All important data is persisted through Docker volumes:

- **Database**: Stored in `./data/zillow_properties.db`
- **Logs**: Stored in `./logs/` directory
- **Exports**: CSV files stored in `./csv_exports/` and `./static/exports/`
- **Configuration**: Mounted from host files

## Security Considerations

- The application runs as a non-root user (`app`)
- Configuration files are mounted as read-only
- Health checks are implemented to monitor application status
- The container uses a slim Python base image to reduce attack surface

## Troubleshooting

### Container won't start
1. Check if port 5001 is already in use:
   ```bash
   lsof -i :5001
   ```

2. Check container logs:
   ```bash
   docker-compose logs
   ```

### Database issues
1. Ensure the `./data` directory exists and has proper permissions:
   ```bash
   mkdir -p data
   chmod 755 data
   ```

2. Check if the database file is accessible:
   ```bash
   ls -la data/
   ```

### Permission issues
1. If you encounter permission issues, ensure the directories are owned by the correct user:
   ```bash
   sudo chown -R $USER:$USER data logs csv_exports static/
   ```

## Production Deployment

For production deployment, consider:

1. **Using a reverse proxy** (nginx, Apache) in front of the Flask app
2. **Setting up SSL/TLS** certificates
3. **Using environment variables** for sensitive configuration
4. **Implementing proper logging** and monitoring
5. **Setting up database backups**
6. **Using a production-grade database** (PostgreSQL, MySQL) instead of SQLite

### Example production docker-compose.yml
```yaml
version: '3.8'

services:
  zillow-app:
    build: .
    container_name: zillow-property-manager
    ports:
      - "127.0.0.1:5001:5001"  # Only bind to localhost
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./csv_exports:/app/csv_exports
      - ./static/exports:/app/static/exports
      - ./static/logs:/app/static/logs
      - ./twilio_config.json:/app/twilio_config.json:ro
      - ./scraper_schedule.json:/app/scraper_schedule.json:ro
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
    restart: unless-stopped
    networks:
      - zillow-network

  nginx:
    image: nginx:alpine
    container_name: zillow-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - zillow-app
    restart: unless-stopped
    networks:
      - zillow-network

networks:
  zillow-network:
    driver: bridge
```

## Support

If you encounter issues with the Docker deployment, please:

1. Check the container logs: `docker-compose logs`
2. Verify all required files are present
3. Ensure proper permissions on mounted volumes
4. Check that port 5001 is not already in use
