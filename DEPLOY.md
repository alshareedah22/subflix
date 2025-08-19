# SubFlix Deployment Guide

## Quick Start (Recommended)

1. **Download the files** to your server
2. **Copy environment template:**
   ```bash
   cp .env.docker .env
   ```

3. **Edit .env with your paths:**
   ```bash
   nano .env
   ```
   Update these lines:
   ```
   MOVIES_SOURCE_PATH=/home/user/movies
   TVSHOWS_SOURCE_PATH=/home/user/tvshows
   MOVIES_OUTPUT_PATH=/home/user/processed/movies
   TVSHOWS_OUTPUT_PATH=/home/user/processed/tvshows
   JWT_SECRET=your-super-secret-key-here
   ```

4. **Start SubFlix:**
   ```bash
   docker-compose up -d
   ```

5. **Access:** http://localhost:3000
   **Login:** admin / admin123

## Manual Docker Build

If you prefer to build manually:

```bash
# Build
docker build -t subflix .

# Run
docker run -d \
  --name subflix \
  -p 3000:80 \
  -v /your/movies:/data/movies:ro \
  -v /your/tvshows:/data/tvshows:ro \
  -v /your/processed/movies:/data/processed/movies \
  -v /your/processed/tvshows:/data/processed/tvshows \
  -e JWT_SECRET=your-secret \
  --link mongodb:mongodb \
  subflix

# MongoDB
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:7.0
```

## Folder Configuration in App

Once logged in, set these paths in Settings:

- **Movies Source:** `/data/movies`
- **Movies Output:** `/data/processed/movies`  
- **TV Shows Source:** `/data/tvshows`
- **TV Shows Output:** `/data/processed/tvshows`

## Production Checklist

- [ ] Change JWT_SECRET in .env
- [ ] Change default admin password
- [ ] Set up HTTPS reverse proxy
- [ ] Configure log rotation
- [ ] Set up MongoDB backups
- [ ] Monitor disk space for processed videos

## Troubleshooting

**No files found:** Check volume mounts match your .env paths
**Processing fails:** Ensure FFmpeg is working: `docker exec subflix ffmpeg -version`
**Login fails:** Check MongoDB connection and logs
**Permission errors:** Ensure Docker can access your media folders