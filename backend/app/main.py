import random
import uuid
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Import our database session dependency and the User model
from app.database import get_db
from app.models import User

# Import S3 utilities
from app.s3 import upload_file_to_s3

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Crux Backend is running!"}


@app.post("/upload-video")
async def upload_climb_video(file: UploadFile = File(...)):
    """
    Uploads a video file to S3 (MinIO) and returns the file URL.
    """
    # 1. Validate file type (basic check)
    if file.content_type not in ["video/mp4", "video/quicktime"]:
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only MP4/MOV allowed."
        )

    # 2. Generate a unique filename to prevent collisions
    # e.g., "videos/uuid-filename.mp4"
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"videos/{uuid.uuid4()}.{file_extension}"

    try:
        # 3. Stream upload to S3
        # file.file is the underlying Python file object which aioboto3 can read
        url = await upload_file_to_s3(file.file, unique_filename)

        return {"status": "success", "filename": unique_filename, "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# TEST ENDPOINT 1: WRITE
# Creates a random user every time you hit it
@app.post("/test/user")
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
@app.get("/test/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    # "select(User)" is the standard SQLAlchemy 2.0 syntax
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
