#!/bin/bash

# Docker setup script for Zillow Property Manager
set -e

echo "🐳 Setting up Zillow Property Manager with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data
mkdir -p logs
mkdir -p csv_exports
mkdir -p static/exports
mkdir -p static/logs

# Set proper permissions
echo "🔐 Setting proper permissions..."
chmod 755 data
chmod 755 logs
chmod 755 csv_exports
chmod 755 static/exports
chmod 755 static/logs

# Check if required config files exist
echo "📋 Checking configuration files..."
if [ ! -f "twilio_config.json" ]; then
    echo "⚠️  Warning: twilio_config.json not found. Creating a template..."
    cat > twilio_config.json << EOF
{
    "account_sid": "your_account_sid_here",
    "auth_token": "your_auth_token_here",
    "from_number": "your_twilio_number_here"
}
EOF
    echo "📝 Please update twilio_config.json with your actual Twilio credentials."
fi

if [ ! -f "scraper_schedule.json" ]; then
    echo "⚠️  Warning: scraper_schedule.json not found. Creating a template..."
    cat > scraper_schedule.json << EOF
{
    "enabled": true,
    "interval_minutes": 10,
    "start_time": "09:00",
    "end_time": "18:00"
}
EOF
    echo "📝 Please update scraper_schedule.json with your desired schedule."
fi

# Build and start the application
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting the application..."
docker-compose up -d

# Wait for the application to start
echo "⏳ Waiting for the application to start..."
sleep 10

# Check if the application is running
if curl -f http://localhost:5001/ > /dev/null 2>&1; then
    echo "✅ Application is running successfully!"
    echo "🌐 Access the application at: http://localhost:5001"
    echo ""
    echo "📊 Useful commands:"
    echo "  View logs: docker-compose logs -f"
    echo "  Stop app:  docker-compose down"
    echo "  Restart:   docker-compose restart"
    echo "  Rebuild:   docker-compose up --build -d"
else
    echo "❌ Application failed to start. Check the logs:"
    echo "   docker-compose logs"
    exit 1
fi
