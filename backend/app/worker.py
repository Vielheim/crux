import os

# Force CPU-only inference — disables EGL/GPU initialization
os.environ["MEDIAPIPE_DISABLE_GPU"] = "1"

import asyncio
import tempfile
import cv2
import mediapipe as mp
from pathlib import Path
from sqlalchemy import select
from arq.connections import RedisSettings

# Project imports
from app.database import async_session_factory
from app.models import Climb, ClimbStatus
from app.s3 import get_s3_client, S3_BUCKET_NAME
from app.redis import REDIS_HOST, REDIS_PORT

# Define local temp directory
TEMP_DIR = Path("/tmp/crux-worker")


# Initialize MediaPipe Pose solution
mp_pose = mp.solutions.pose


def run_pose_estimation(video_path: str):
    """
    Synchronous Computer Vision task.
    Runs in a separate thread to avoid blocking the async event loop.
    """
    results_payload = []

    with mp_pose.Pose(
        static_image_mode=False,
        enable_segmentation=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image_rgb)

            if results.pose_landmarks:
                landmarks = [
                    {"x": lm.x, "y": lm.y, "z": lm.z, "v": lm.visibility}
                    for lm in results.pose_landmarks.landmark
                ]
                results_payload.append(landmarks)
            else:
                results_payload.append(None)

        cap.release()

    processed_count = len(results_payload)
    if total_frames > 0 and processed_count < (total_frames * 0.9):
        raise ValueError(
            f"Video analysis incomplete. Expected {total_frames} frames, but processed {processed_count}."
        )

    return results_payload


async def analyze_climb(ctx, climb_id: int, file_key: str):
    """
    Background job triggered by ARQ.
    Downloads video to local tmp -> Runs CV Analysis -> Updates DB.
    """
    print(f"[Worker] Starting analysis for Climb ID: {climb_id}")

    # Ensure local tmp directory exists
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Create temp file in our specific local directory
    fd, tmp_path = tempfile.mkstemp(suffix=".mp4", dir=TEMP_DIR)
    os.close(fd)

    async with async_session_factory() as session:
        try:
            # 1. Update Status to PROCESSING
            stmt = select(Climb).where(Climb.id == climb_id)
            result = await session.execute(stmt)
            climb = result.scalars().first()

            if not climb:
                print(f"[Worker] Climb {climb_id} not found.")
                return

            climb.status = ClimbStatus.PROCESSING
            await session.commit()

            # 2. Download Video from S3
            # Safely extract the exact object key if a full URL was passed
            print(f"[Worker] Extracting S3 key from URL: {file_key}")
            if "http" in file_key:
                # Splits 'http://minio:9000/crux-videos/videos/123.mp4' -> 'videos/123.mp4'
                actual_file_key = file_key.split(f"/{S3_BUCKET_NAME}/")[-1]
            else:
                actual_file_key = file_key

            print(f"[Worker] Downloading S3 key '{actual_file_key}' to {tmp_path}...")
            async with await get_s3_client() as s3:
                await s3.download_file(S3_BUCKET_NAME, actual_file_key, tmp_path)
                print("[Worker] Download completed.")

            # 3. Run CV Logic
            print(f"[Worker] Running pose estimation...")
            pose_data = await asyncio.to_thread(run_pose_estimation, tmp_path)

            # 4. Save Results
            climb.analysis_results = {"pose_data": pose_data}
            climb.status = ClimbStatus.COMPLETED
            await session.commit()
            print(f"[Worker] Analysis for Climb {climb_id} completed successfully.")

        except Exception as e:
            print(f"[Worker] Error analyzing climb {climb_id}: {str(e)}")
            await session.rollback()

            stmt = select(Climb).where(Climb.id == climb_id)
            result = await session.execute(stmt)
            climb = result.scalars().first()
            if climb:
                climb.status = ClimbStatus.FAILED
                climb.analysis_results = {"error": str(e)}
                await session.commit()

        finally:
            # 5. Cleanup Temp File
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


async def startup(ctx):
    print("[Worker] Starting up...")


async def shutdown(ctx):
    print("[Worker] Shutting down...")


class WorkerSettings:
    on_startup = startup
    on_shutdown = shutdown
    functions = [analyze_climb]
    redis_settings = RedisSettings(host=REDIS_HOST, port=int(REDIS_PORT))
