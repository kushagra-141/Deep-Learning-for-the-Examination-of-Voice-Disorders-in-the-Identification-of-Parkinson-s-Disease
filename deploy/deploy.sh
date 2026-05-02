#!/bin/bash

# deploy.sh - Deployment script for Parkinson's Detection App
# Usage: ./deploy.sh [branch_name]

set -e

BRANCH=${1:-main}

echo "--- Starting Deployment (Branch: $BRANCH) ---"

# 1. Pull latest code
echo "Pulling latest code from origin/$BRANCH..."
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH

# 2. Check for .env file
if [ ! -f .env ]; then
    echo "WARNING: .env file not found! Creating from .env.example..."
    cp .env.example .env
    echo "IMPORTANT: Please edit .env with your production API keys before continuing."
    exit 1
fi

# 3. Build and restart containers
echo "Rebuilding and restarting Docker containers..."
docker-compose down
docker-compose up --build -d

# 4. Clean up old images
echo "Cleaning up dangling Docker images..."
docker image prune -f

echo "--- Deployment Complete! ---"
echo "Application should be running at: http://$(curl -s ifconfig.me)"
echo "Use 'docker-compose logs -f' to monitor status."
