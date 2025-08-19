# Multi-stage Docker build for SubFlix
FROM node:20-slim as frontend-build

# Build frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile
COPY frontend/ .
RUN yarn build

# Main application image
FROM python:3.11-slim

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./backend/

# Copy frontend build from previous stage
COPY --from=frontend-build /app/frontend/build ./frontend/build/

# Copy configuration files
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/nginx.conf /etc/nginx/sites-available/default

# Create directories for logs and data
RUN mkdir -p /var/log/supervisor \
    /app/data/movies \
    /app/data/tvshows \
    /app/data/processed/movies \
    /app/data/processed/tvshows

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV NODE_ENV=production
ENV MONGO_URL=mongodb://mongodb:27017
ENV DB_NAME=subflix
ENV CORS_ORIGINS=*
ENV JWT_SECRET=your-secret-key-change-in-production

# Expose ports
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:80/api/ || exit 1

# Start supervisor to manage all services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]