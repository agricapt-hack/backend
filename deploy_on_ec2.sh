#!/bin/bash
set -e

DOCKER_FILE="$1"
IMAGE_NAME="$2"
APP_PORT="$3"

# Kill any process using the specified port
if lsof -i :"$APP_PORT" &>/dev/null; then
  echo "🔴 Killing process on port $APP_PORT..."
  kill -9 $(lsof -t -i :"$APP_PORT")
fi

# Remove any container using the specified port
CONTAINER_ID=$(docker ps -q --filter "publish=$APP_PORT")
if [ -n "$CONTAINER_ID" ]; then
  echo "🛑 Stopping and removing container using port $APP_PORT..."
  docker stop "$CONTAINER_ID"
  docker rm "$CONTAINER_ID"
fi

DOCKER_FILE="$1"
IMAGE_NAME="$2"
APP_PORT="$3"

# Install Docker if missing
if ! command -v docker &> /dev/null
then
  echo "🚀 Installing Docker..."
  sudo apt-get update
  sudo apt-get install -y docker.io
  sudo systemctl enable docker
  sudo systemctl start docker
  sudo usermod -aG docker $USER
  echo "Docker installed and user added to docker group"
fi

docker stop "$IMAGE_NAME" || true
docker rm "$IMAGE_NAME" || true
docker build -f "$DOCKER_FILE" -t "$IMAGE_NAME:latest" .
docker run -d --name "$IMAGE_NAME" -p "$APP_PORT:$APP_PORT" "$IMAGE_NAME:latest"
