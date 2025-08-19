# SubFlix - Subtitle Embedding Tool

A Radarr/Sonarr-inspired web application for embedding subtitles into video files without quality loss.

## Features

- 🎬 **Dual Content Management**: Separate configurations for Movies and TV Shows
- 📁 **Smart File Discovery**: Auto-scan folders for videos (.mp4, .mkv, .ts) and subtitles (.srt, .vtt, .sub)
- 🔗 **Intelligent Pairing**: Auto-match videos with subtitles by language (.ar.srt, .en.srt, .ara.srt, .eng.srt)
- ⚡ **Fast Subtitle Embedding**: Uses FFmpeg to embed (not burn) subtitles without re-encoding
- ☁️ **BunnyCDN Integration**: Optional upload to storage or stream services
- 🔐 **Admin Authentication**: Secure login system with JWT tokens
- 📊 **Real-time Monitoring**: Job queue with progress tracking
- 🌙 **Dark Theme**: Professional Radarr-inspired interface

## Quick Start with Docker

### 1. Clone and Setup

```bash
git clone <your-repo>
cd subflix
cp .env.docker .env
```

### 2. Configure Your Media Paths

Edit the `.env` file with your actual folder paths:

```bash
# Update these paths to match your setup
MOVIES_SOURCE_PATH=/home/user/movies
TVSHOWS_SOURCE_PATH=/home/user/tvshows
MOVIES_OUTPUT_PATH=/home/user/processed/movies
TVSHOWS_OUTPUT_PATH=/home/user/processed/tvshows

# Change this in production!
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
```

### 3. Run with Docker Compose

```bash
docker-compose up -d
```

### 4. Access the Application

- **Web Interface**: http://localhost:3000
- **Default Login**: `admin` / `admin123`

## Manual Docker Build

```bash
# Build the image
docker build -t subflix .

# Run with custom volumes
docker run -d \
  --name subflix \
  -p 3000:80 \
  -v /path/to/your/movies:/data/movies:ro \
  -v /path/to/your/tvshows:/data/tvshows:ro \
  -v /path/to/processed/movies:/data/processed/movies \
  -v /path/to/processed/tvshows:/data/processed/tvshows \
  -e JWT_SECRET=your-secret-key \
  subflix
```

## Configuration

### In-App Settings

Once logged in, configure the following paths in Settings:

- **Movies Source**: `/data/movies` (where your movie files + subtitles are)
- **Movies Output**: `/data/processed/movies` (where processed movies go)
- **TV Shows Source**: `/data/tvshows` (where your TV show files + subtitles are)
- **TV Shows Output**: `/data/processed/tvshows` (where processed TV shows go)

### Folder Structure Example

**Source Folders:**
```
/home/user/movies/
├── TheMask(1994)/
│   ├── TheMask(1994).mp4
│   └── TheMask(1994).ar.srt
└── Superman(1978)/
    ├── Superman(1978).mp4
    └── Superman(1978).ar.srt
```

**Output Result:**
```
/home/user/processed/movies/
├── TheMask(1994).ar.mp4      # With embedded Arabic subtitles
└── Superman(1978).ar.mp4     # With embedded Arabic subtitles
```

## Supported Formats

### Video Files
- `.mp4` (MP4)
- `.mkv` (Matroska)
- `.ts` (Transport Stream)

### Subtitle Files
- `.srt` (SubRip)
- `.vtt` (WebVTT)
- `.sub` (Various subtitle formats)

### Language Detection
- `.ar.srt` (Arabic)
- `.en.srt` (English)
- `.ara.srt` (Arabic alternative)
- `.eng.srt` (English alternative)

## How It Works

1. **Scan**: SubFlix scans your source folders for video files
2. **Pair**: Automatically matches video files with their subtitle files
3. **Queue**: You select which files to process
4. **Embed**: FFmpeg embeds subtitles without re-encoding (fast!)
5. **Save**: Processed files are saved to your output folders
6. **Upload**: Optionally upload to BunnyCDN

## Processing Details

- **Method**: Subtitle embedding (not burning)
- **Speed**: ~2-5 minutes for a 2-hour movie
- **Quality**: No loss - maintains original video encoding
- **Output**: Original filename + language (e.g., `Movie.ar.mp4`)

## Security

- **Authentication**: JWT-based login system
- **Default Credentials**: `admin` / `admin123` (change after first login)
- **Token Expiry**: 24-hour sessions
- **API Protection**: All endpoints require authentication

## Development

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --reload

# Frontend
cd frontend
yarn install
yarn start
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URL` | MongoDB connection string | `mongodb://mongodb:27017` |
| `DB_NAME` | Database name | `subflix` |
| `JWT_SECRET` | JWT signing secret | `your-secret-key-change-in-production` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

## Troubleshooting

### Common Issues

1. **"No video files found"**: Check your volume mounts and folder paths
2. **"Processing failed"**: Ensure FFmpeg is installed and working
3. **"Authentication failed"**: Check if MongoDB is running and accessible
4. **"Permission denied"**: Ensure Docker has access to your media folders

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f subflix
docker-compose logs -f mongodb
```

### Health Check

```bash
# Check if services are healthy
docker-compose ps

# Test API endpoint
curl http://localhost:3000/health
```

## Production Deployment

1. **Change JWT Secret**: Update `JWT_SECRET` in `.env`
2. **Use HTTPS**: Configure reverse proxy (nginx/traefik)
3. **Backup Database**: Regular MongoDB backups
4. **Monitor Logs**: Set up log rotation and monitoring
5. **Resource Limits**: Configure appropriate CPU/memory limits

## License

[Your License Here]

## Support

For issues and questions, please create an issue in the GitHub repository.