#!/bin/sh

set -e

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
export JOBLIB_TEMP_FOLDER=/tmp
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
