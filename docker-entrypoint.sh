#!/bin/bash
set -e

# Create necessary directories if they don't exist
mkdir -p /app/data
mkdir -p /app/logs
mkdir -p /app/csv_exports
mkdir -p /app/static/exports
mkdir -p /app/static/logs

# Set proper permissions
chown -R app:app /app/data
chown -R app:app /app/logs
chown -R app:app /app/csv_exports
chown -R app:app /app/static/exports
chown -R app:app /app/static/logs

# Execute the main command
exec "$@"
