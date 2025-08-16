#!/bin/bash
set -e

DOCKER_FILE="$1"
IMAGE_NAME="$2"
APP_PORT="$3"

# Install Docker if missing
if ! command -v docker &> /dev/null
then
  echo '🚀 Installing Docker...'
  sudo apt-get update
  sudo apt-get install -y docker.io
  sudo systemctl enable docker
  sudo systemctl start docker
  sudo usermod -aG docker $USER
  echo "Docker installed and user added to docker group"
fi