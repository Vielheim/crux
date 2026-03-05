import random
import uuid
from fastapi import (
    FastAPI,
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from typing import List  # Make sure to import List at the top of main.py

# Import our database session dependency and the User model
from app.database import get_db
from app.models import Climb, User
from app.schemas import ClimbResponse

# Import S3 utilities
from app.s3 import upload_file_to_s3, delete_file_from_s3, S3_BUCKET_NAME
from app.redis import get_redis_pool


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create Redis Pool
    app.state.arq_pool = await get_redis_pool()
    print("Redis pool created.")
    yield

    # Shutdown: Close Redis Pool
    await app.state.arq_pool.close()
    print("Redis pool closed.")


app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")


@api_router.get("/")
def read_root():
    return {"message": "Crux Backend is running!"}


@api_router.post("/upload-video", response_model=ClimbResponse)
async def upload_climb_video(
    request: Request,
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Uploads a video file to S3 (MinIO) and returns the file URL.
    """
    # Verify User Exists (Prevent Foreign Key Constraint Errors)
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file type
    if file.content_type not in ["video/mp4", "video/quicktime"]:
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only MP4/MOV allowed."
        )

    # Generate a unique filename and upload to S3
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"videos/{uuid.uuid4()}.{file_extension}"

    try:
        # file.file is the underlying Python file object which aioboto3 can read
        url = await upload_file_to_s3(file.file, unique_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Create Database Record
    # We don't need to set status=PENDING manually as it is the default in the model
    new_climb = Climb(user_id=user_id, video_url=url)

    db.add(new_climb)
    await db.commit()
    await db.refresh(new_climb)

    # Enqueue Job to Arq (Redis)
    # We access the pool from app.state
    # "analyze_climb" will be the function name in our worker
    try:
        await request.app.state.arq_pool.enqueue_job(
            "analyze_climb", climb_id=new_climb.id, file_key=url
        )
    except Exception as e:
        # In a real app, you might want to rollback the DB or mark status as FAILED here
        print(f"Failed to enqueue job: {e}")

    return new_climb


@api_router.get("/climb/{climb_id}", response_model=ClimbResponse)
async def get_climb(climb_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Climb).where(Climb.id == climb_id))
    climb = result.scalars().first()
    if not climb:
        raise HTTPException(status_code=404, detail="Climb not found")
    return climb


# Fetches all climbs from the DB for a user
@api_router.get("/climbs/{user_id}", response_model=List[ClimbResponse])
async def get_climbs_for_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Climb).where(Climb.user_id == user_id))
    climbs = result.scalars().all()
    return climbs


@api_router.delete("/climb/{climb_id}")
async def delete_climb(climb_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a climb record from the database and removes the associated video from S3.
    """
    # 1. Fetch the climb
    result = await db.execute(select(Climb).where(Climb.id == climb_id))
    climb = result.scalars().first()

    if not climb:
        raise HTTPException(status_code=404, detail="Climb not found")

    # 2. Extract S3 Object Key from URL
    # URL format: http://endpoint/bucket_name/videos/filename.mp4
    # We need to extract: videos/filename.mp4
    bucket_prefix = f"/{S3_BUCKET_NAME}/"
    if bucket_prefix in climb.video_url:
        object_name = climb.video_url.split(bucket_prefix)[-1]
        try:
            await delete_file_from_s3(object_name)
        except Exception as e:
            # We log the error but don't fail the request to ensure the DB record
            # can still be cleaned up (prevents "ghost" records in the UI).
            print(f"Failed to delete S3 object {object_name}: {e}")

    # 3. Delete from Database
    await db.delete(climb)
    await db.commit()

    return {"status": "success", "message": f"Climb {climb_id} deleted."}


# TEST ENDPOINT 1: WRITE
# Creates a random user every time you hit it
@api_router.post("/test/user")
async def test_create_user(db: AsyncSession = Depends(get_db)):
    # Generate a random suffix to avoid "Unique Constraint" errors on re-runs
    suffix = random.randint(1000, 9999)

    new_user = User(username=f"climber_{suffix}", email=f"climber_{suffix}@crux.com")

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)  # Reloads the object with the ID assigned by DB

    return {"status": "success", "created_user": new_user}


# TEST ENDPOINT 2: READ
# Fetches all users from the DB
@api_router.get("/test/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    # "select(User)" is the standard SQLAlchemy 2.0 syntax
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


# Register the router with the main FastAPI application
app.include_router(api_router)
