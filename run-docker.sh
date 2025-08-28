#!/bin/bash

# Simple Docker run script for Zillow Property Manager
set -e

echo "🐳 Building Zillow Property Manager Docker image..."

# Build the Docker image
docker build -t zillow-property-manager .

echo "🚀 Running Zillow Property Manager container..."

# Run the container
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

echo "✅ Container started successfully!"
echo "🌐 Access the application at: http://localhost:5001"
echo ""
echo "📊 Useful commands:"
echo "  View logs:    docker logs -f zillow-app"
echo "  Stop app:     docker stop zillow-app"
echo "  Remove app:   docker rm zillow-app"
echo "  Restart app:  docker restart zillow-app"
