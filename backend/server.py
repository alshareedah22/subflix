from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
import subprocess
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import json
import hashlib
import jwt


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="SubFlix - Subtitle Embedding Tool")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class LoginRequest(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    is_admin: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class Settings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    movies_source_path: str = ""
    movies_output_path: str = ""
    tvshows_source_path: str = ""
    tvshows_output_path: str = ""
    bunnycdn_api_key: str = ""
    bunnycdn_storage_zone: str = ""
    bunnycdn_base_url: str = ""
    bunnycdn_service_type: str = "storage"  # storage or stream
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SettingsUpdate(BaseModel):
    movies_source_path: Optional[str] = None
    movies_output_path: Optional[str] = None
    tvshows_source_path: Optional[str] = None
    tvshows_output_path: Optional[str] = None
    bunnycdn_api_key: Optional[str] = None
    bunnycdn_storage_zone: Optional[str] = None
    bunnycdn_base_url: Optional[str] = None
    bunnycdn_service_type: Optional[str] = None

class VideoFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str
    file_name: str
    file_size: int
    subtitle_path: Optional[str] = None
    subtitle_language: Optional[str] = None
    content_type: str  # "movie" or "tvshow"
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProcessingJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    video_file_id: str
    input_video_path: str
    input_subtitle_path: str
    output_path: str
    status: str = "queued"  # queued, processing, completed, failed
    progress: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ScanRequest(BaseModel):
    content_type: str  # "movies" or "tvshows"


# Helper functions
def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

def create_jwt_token(user_data: dict) -> str:
    """Create a JWT token"""
    payload = {
        'user_id': user_data['id'],
        'username': user_data['username'],
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    """Decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    user_data = await db.users.find_one({"id": payload['user_id']})
    if not user_data:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_data)

async def create_default_admin():
    """Create default admin user if none exists"""
    admin_exists = await db.users.find_one({"username": "admin"})
    if not admin_exists:
        admin_user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            is_admin=True
        )
        await db.users.insert_one(admin_user.dict())
        logging.info("Default admin user created: admin/admin123")

def find_video_files(directory: str, extensions: List[str] = [".mp4", ".mkv", ".ts"]) -> List[Dict[str, Any]]:
    """Scan directory for video files"""
    if not os.path.exists(directory):
        return []
    
    video_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                file_stat = os.stat(file_path)
                
                video_files.append({
                    "file_path": file_path,
                    "file_name": file,
                    "file_size": file_stat.st_size,
                    "directory": root
                })
    
    return video_files

def find_subtitle_for_video(video_path: str, subtitle_extensions: List[str] = [".srt", ".vtt", ".sub"]) -> Optional[Dict[str, str]]:
    """Find matching subtitle file for a video"""
    video_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Language patterns to look for
    language_patterns = [".ar", ".en", ".ara", ".eng"]
    
    for file in os.listdir(video_dir):
        if any(file.lower().endswith(ext) for ext in subtitle_extensions):
            subtitle_name = os.path.splitext(file)[0]
            
            # Check if subtitle matches video name pattern
            if subtitle_name.startswith(video_name):
                for lang_pattern in language_patterns:
                    if lang_pattern in subtitle_name.lower():
                        return {
                            "path": os.path.join(video_dir, file),
                            "language": lang_pattern.replace(".", "")
                        }
                
                # If no language pattern found but name matches, assume it's a match
                return {
                    "path": os.path.join(video_dir, file),
                    "language": "unknown"
                }
    
    return None

async def embed_subtitles(input_video: str, input_subtitle: str, output_path: str, job_id: str) -> bool:
    """Embed subtitles into video using FFmpeg"""
    try:
        # Update job status
        await db.processing_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "processing",
                "started_at": datetime.now(timezone.utc),
                "progress": 10
            }}
        )
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # FFmpeg command to embed subtitles (no re-encoding, just container change)
        cmd = [
            "ffmpeg", "-y",  # -y to overwrite output file
            "-i", input_video,
            "-i", input_subtitle,
            "-c", "copy",  # Copy all streams without re-encoding
            "-c:s", "srt",  # Subtitle codec
            "-map", "0",    # Map all streams from first input
            "-map", "1",    # Map subtitle from second input
            output_path
        ]
        
        # Update progress
        await db.processing_jobs.update_one(
            {"id": job_id},
            {"$set": {"progress": 30}}
        )
        
        # Run FFmpeg command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Success
            await db.processing_jobs.update_one(
                {"id": job_id},
                {"$set": {
                    "status": "completed",
                    "progress": 100,
                    "completed_at": datetime.now(timezone.utc)
                }}
            )
            
            # Update video file status
            job_data = await db.processing_jobs.find_one({"id": job_id})
            if job_data:
                await db.video_files.update_one(
                    {"id": job_data["video_file_id"]},
                    {"$set": {"status": "completed"}}
                )
            
            return True
        else:
            # Error occurred
            error_msg = stderr.decode() if stderr else "Unknown error"
            await db.processing_jobs.update_one(
                {"id": job_id},
                {"$set": {
                    "status": "failed",
                    "error_message": error_msg,
                    "completed_at": datetime.now(timezone.utc)
                }}
            )
            return False
            
    except Exception as e:
        # Exception occurred
        await db.processing_jobs.update_one(
            {"id": job_id},
            {"$set": {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(timezone.utc)
            }}
        )
        return False


# Authentication Routes
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    user_data = await db.users.find_one({"username": login_request.username})
    
    if not user_data or not verify_password(login_request.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    token = create_jwt_token(user_data)
    
    return LoginResponse(
        access_token=token,
        user={
            "id": user_data["id"],
            "username": user_data["username"],
            "is_admin": user_data["is_admin"]
        }
    )

# API Routes (Protected)
@api_router.get("/")
async def root(current_user: User = Depends(get_current_user)):
    return {"message": "SubFlix - Subtitle Embedding Tool API", "user": current_user.username}

@api_router.get("/settings", response_model=Settings)
async def get_settings(current_user: User = Depends(get_current_user)):
    settings = await db.settings.find_one({}, sort=[("created_at", -1)])
    if not settings:
        # Create default settings
        default_settings = Settings()
        await db.settings.insert_one(default_settings.dict())
        return default_settings
    return Settings(**settings)

@api_router.put("/settings", response_model=Settings)
async def update_settings(settings_update: SettingsUpdate, current_user: User = Depends(get_current_user)):
    existing_settings = await db.settings.find_one({}, sort=[("created_at", -1)])
    
    if existing_settings:
        # Update existing settings
        update_data = {k: v for k, v in settings_update.dict().items() if v is not None}
        await db.settings.update_one(
            {"id": existing_settings["id"]},
            {"$set": update_data}
        )
        updated_settings = await db.settings.find_one({"id": existing_settings["id"]})
        return Settings(**updated_settings)
    else:
        # Create new settings
        new_settings = Settings(**settings_update.dict(exclude_none=True))
        await db.settings.insert_one(new_settings.dict())
        return new_settings

@api_router.post("/scan")
async def scan_folders(scan_request: ScanRequest, current_user: User = Depends(get_current_user)):
    settings = await db.settings.find_one({}, sort=[("created_at", -1)])
    if not settings:
        raise HTTPException(status_code=400, detail="Settings not configured")
    
    content_type = scan_request.content_type
    if content_type == "movies":
        source_path = settings.get("movies_source_path")
    elif content_type == "tvshows":
        source_path = settings.get("tvshows_source_path")
    else:
        raise HTTPException(status_code=400, detail="Invalid content type")
    
    if not source_path:
        raise HTTPException(status_code=400, detail=f"Source path for {content_type} not configured")
    
    # Find video files
    video_files = find_video_files(source_path)
    
    scanned_files = []
    for video_data in video_files:
        # Find matching subtitle
        subtitle_info = find_subtitle_for_video(video_data["file_path"])
        
        video_file = VideoFile(
            file_path=video_data["file_path"],
            file_name=video_data["file_name"],
            file_size=video_data["file_size"],
            content_type=content_type,
            subtitle_path=subtitle_info["path"] if subtitle_info else None,
            subtitle_language=subtitle_info["language"] if subtitle_info else None
        )
        
        # Save to database
        await db.video_files.insert_one(video_file.dict())
        scanned_files.append(video_file)
    
    return {"scanned_files": len(scanned_files), "files": scanned_files}

@api_router.get("/video-files", response_model=List[VideoFile])
async def get_video_files(current_user: User = Depends(get_current_user), content_type: Optional[str] = None):
    query = {}
    if content_type:
        query["content_type"] = content_type
    
    video_files = await db.video_files.find(query).sort("created_at", -1).to_list(1000)
    return [VideoFile(**video_file) for video_file in video_files]

@api_router.post("/process/{video_file_id}")
async def process_video(video_file_id: str, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    # Get video file
    video_file_data = await db.video_files.find_one({"id": video_file_id})
    if not video_file_data:
        raise HTTPException(status_code=404, detail="Video file not found")
    
    video_file = VideoFile(**video_file_data)
    
    if not video_file.subtitle_path:
        raise HTTPException(status_code=400, detail="No subtitle file found for this video")
    
    # Get settings for output path
    settings = await db.settings.find_one({}, sort=[("created_at", -1)])
    if not settings:
        raise HTTPException(status_code=400, detail="Settings not configured")
    
    # Determine output path
    if video_file.content_type == "movies":
        output_base = settings.get("movies_output_path")
    else:
        output_base = settings.get("tvshows_output_path")
    
    if not output_base:
        raise HTTPException(status_code=400, detail=f"Output path for {video_file.content_type} not configured")
    
    # Generate output filename
    input_name = os.path.splitext(video_file.file_name)[0]
    input_ext = os.path.splitext(video_file.file_name)[1]
    output_filename = f"{input_name}.{video_file.subtitle_language}{input_ext}"
    output_path = os.path.join(output_base, output_filename)
    
    # Create processing job
    job = ProcessingJob(
        video_file_id=video_file_id,
        input_video_path=video_file.file_path,
        input_subtitle_path=video_file.subtitle_path,
        output_path=output_path
    )
    
    await db.processing_jobs.insert_one(job.dict())
    
    # Update video file status
    await db.video_files.update_one(
        {"id": video_file_id},
        {"$set": {"status": "processing"}}
    )
    
    # Start background processing
    background_tasks.add_task(
        embed_subtitles,
        video_file.file_path,
        video_file.subtitle_path,
        output_path,
        job.id
    )
    
    return {"message": "Processing started", "job_id": job.id}

@api_router.get("/jobs", response_model=List[ProcessingJob])
async def get_processing_jobs(current_user: User = Depends(get_current_user)):
    jobs = await db.processing_jobs.find().sort("created_at", -1).to_list(1000)
    return [ProcessingJob(**job) for job in jobs]

@api_router.get("/jobs/{job_id}", response_model=ProcessingJob)
async def get_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    job_data = await db.processing_jobs.find_one({"id": job_id})
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
    return ProcessingJob(**job_data)

@api_router.delete("/video-files")
async def clear_video_files(current_user: User = Depends(get_current_user)):
    await db.video_files.delete_many({})
    return {"message": "All video files cleared"}

@api_router.delete("/jobs")
async def clear_jobs(current_user: User = Depends(get_current_user)):
    await db.processing_jobs.delete_many({})
    return {"message": "All jobs cleared"}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await create_default_admin()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()