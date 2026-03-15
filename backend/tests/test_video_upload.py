import pytest
from unittest.mock import patch, AsyncMock
from app.models import User, Climb
from app.main import app  # Needed to access app.state.arq_pool


@pytest.mark.asyncio
async def test_upload_climb_video_success(client, db_session):
    # SETUP: Create a dummy user in the test DB
    user = User(username="test_climber", email="test@crux.com")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # MOCK: Mock the S3 upload function to return a fake URL
    # We patch 'app.main.upload_file_to_s3' because that's where it is imported
    with patch("app.main.upload_file_to_s3", new_callable=AsyncMock) as mock_s3:
        mock_s3.return_value = "http://minio/bucket/videos/test-video.mp4"

        # ACTION: Send Multipart Request
        # Note: We must send 'user_id' as data (form) and 'file' as files
        response = await client.post(
            "/upload-video",
            data={"user_id": user.id},
            files={"file": ("climb.mp4", b"fake video bytes", "video/mp4")},
        )

    # ASSERT: Check Response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["video_url"] == "http://minio/bucket/videos/test-video.mp4"
    assert data["status"] == "PENDING"

    # VERIFY DB: Ensure the Climb record was actually created
    # We use a new query to check the DB state
    from sqlalchemy import select

    result = await db_session.execute(select(Climb).where(Climb.id == data["id"]))
    climb_in_db = result.scalars().first()

    assert climb_in_db is not None
    assert climb_in_db.user_id == user.id
    assert climb_in_db.status == "PENDING"
    assert climb_in_db.video_url == "http://minio/bucket/videos/test-video.mp4"

    # ASSERT: Job Enqueued
    # Check that our mocked pool received the job
    mock_pool = app.state.arq_pool
    mock_pool.enqueue_job.assert_called_once()

    # Check arguments: function name and keyword args
    call_args = mock_pool.enqueue_job.call_args
    assert call_args[0][0] == "analyze_climb"
    assert call_args[1]["climb_id"] == data["id"]
    assert call_args[1]["video_url"] == "http://minio/bucket/videos/test-video.mp4"


@pytest.mark.asyncio
async def test_upload_climb_invalid_user(client):
    """Test uploading with a non-existent user ID"""
    response = await client.post(
        "/upload-video",
        data={"user_id": 9999},  # ID that doesn't exist
        files={"file": ("climb.mp4", b"bytes", "video/mp4")},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_upload_climb_invalid_file_type(client, db_session):
    """Test uploading a text file instead of video"""
    user = User(username="test_climber_2", email="test2@crux.com")
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/upload-video",
        data={"user_id": user.id},
        files={"file": ("document.txt", b"text", "text/plain")},
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]
