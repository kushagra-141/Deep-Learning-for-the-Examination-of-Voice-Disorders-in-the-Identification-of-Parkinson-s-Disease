#!/bin/bash

# setup.sh - Initial server setup for Parkinson's Detection App on Ubuntu EC2
# This script installs Docker and Docker Compose.

set -e

echo "--- Starting EC2 Setup ---"

# 1. Update system packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. Install Docker
echo "Installing Docker..."
# Remove conflicting pre-installed packages
sudo apt-get remove -y docker-compose-v2

sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 3. Add current user to docker group (requires logout/login or 'newgrp docker')
echo "Adding user to docker group..."
sudo usermod -aG docker $USER

# 4. Install Docker Compose (standalone)
echo "Installing Docker Compose standalone..."
DOCKER_COMPOSE_VERSION="v2.24.1"
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. Verify installations
echo "--- Verifying Installations ---"
docker --version
docker-compose --version

echo "--- Setup Complete! ---"
echo "IMPORTANT: Please log out and log back in to apply the 'docker' group changes."
