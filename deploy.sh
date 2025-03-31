#!/bin/bash

# Deployment script for Finance FAQ Chatbot

echo "Deploying Finance FAQ Chatbot..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file with your OPENAI_API_KEY before deploying."
    exit 1
fi

# Pull latest changes if this is a git repository
if [ -d .git ]; then
    echo "Pulling latest changes..."
    git pull
fi

# Build and start the containers
echo "Building and starting containers..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo "Deployment complete! The application is running at http://localhost:8000"
echo "API documentation is available at http://localhost:8000/docs" 