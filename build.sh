#!/bin/bash

echo "🚀 Building SubFlix Docker Image..."
echo "================================"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed or not in PATH"
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.docker .env
    echo "⚠️  Please edit .env file with your actual paths!"
fi

echo "🔨 Building SubFlix container..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo ""
    echo "🎯 To start SubFlix:"
    echo "   docker-compose up -d"
    echo ""
    echo "🌐 Access at: http://localhost:3000"
    echo "🔑 Login: admin / admin123"
    echo ""
    echo "⚠️  Remember to:"
    echo "   1. Edit .env file with your media paths"
    echo "   2. Change the JWT_SECRET in production"
    echo "   3. Change default admin password"
else
    echo "❌ Build failed!"
    exit 1
fi