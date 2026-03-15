import os

# Force CPU-only inference — disables EGL/GPU initialization
os.environ["MEDIAPIPE_DISABLE_GPU"] = "1"

import asyncio
import tempfile
import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
from sqlalchemy import select
from arq.connections import RedisSettings
from sklearn.cluster import KMeans

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
                frame_height, frame_width, _ = frame.shape
                landmarks = [
                    {
                        "x": lm.x * frame_width,
                        "y": lm.y * frame_height,
                        "z": lm.z,
                        "v": lm.visibility,
                    }
                    for lm in results.pose_landmarks.landmark
                ]
                results_payload.append(landmarks)
            else:
                results_payload.append(None)

        cap.release()

    processed_count = len(results_payload)
    if total_frames > 0 and processed_count < (total_frames * 0.95):
        raise ValueError(
            f"Video analysis incomplete. Expected {total_frames} frames, but processed {processed_count}."
        )

    return results_payload


def infer_route_color_from_video(video_path: str, pose_data: list):
    """
    Infers route color by sampling pixels around the climber's hands and feet
    in the first frame where a pose is successfully detected.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    try:
        # Find the first frame with valid pose landmarks
        first_pose_frame_idx = -1
        for i, landmarks in enumerate(pose_data):
            if landmarks:
                first_pose_frame_idx = i
                break

        if first_pose_frame_idx == -1:
            print("[Worker] No pose detected in any frame.")
            return None

        # Seek to the exact frame in the video
        cap.set(cv2.CAP_PROP_POS_FRAMES, first_pose_frame_idx)
        success, frame = cap.read()
        if not success:
            return None

        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        frame_height, frame_width, _ = frame.shape
        
        # Get landmarks for hands (wrists) and feet (ankles)
        # Wrist indices: 15, 16. Ankle indices: 27, 28
        limb_indices = [15, 16, 27, 28]
        landmarks = pose_data[first_pose_frame_idx]

        color_samples = []
        sample_radius = 10  # pixels

        for idx in limb_indices:
            landmark = landmarks[idx]
            # Ensure the landmark is within the frame bounds
            cx, cy = int(landmark["x"]), int(landmark["y"])
            
            if (cx > 0 and cx < frame_width and cy > 0 and cy < frame_height):
                # Define a bounding box for the ROI
                x1 = max(0, cx - sample_radius)
                y1 = max(0, cy - sample_radius)
                x2 = min(frame_width, cx + sample_radius)
                y2 = min(frame_height, cy + sample_radius)

                # Extract the ROI and append its pixels to our samples
                roi = hsv_frame[y1:y2, x1:x2]
                # Reshape and add to list, avoiding empty ROIs
                if roi.size > 0:
                    color_samples.extend(roi.reshape(-1, 3))

        if not color_samples:
            print("[Worker] Could not sample any colors from limb locations.")
            return None

        # Use K-Means on the sampled colors to find the dominant hold color
        # n_clusters=2 assumes one color for the hold and one for the wall/shadows
        kmeans = KMeans(n_clusters=2, init="k-means++", n_init="auto", random_state=42)
        kmeans.fit(np.array(color_samples))
        
        # Heuristic: assume the hold color is the more saturated one.
        most_saturated_cluster_idx = np.argmax(kmeans.cluster_centers_[:, 1])
        hold_color_hsv = kmeans.cluster_centers_[most_saturated_cluster_idx]
        
        print(f"[Worker] Inferred hold color (HSV): {hold_color_hsv}")
        return hold_color_hsv

    finally:
        cap.release()


def run_route_detection(video_path: str, hold_color_hsv: np.ndarray):
    """
    Identifies climbing holds of a specific color in the first frame of a video.
    """
    if hold_color_hsv is None:
        return []

    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    cap.release()

    if not success:
        return []

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define a color range around the detected hold color.
    hue_sensitivity = 15
    saturation_sensitivity = 75
    value_sensitivity = 75

    lower_bound = np.array(
        [
            max(0, hold_color_hsv[0] - hue_sensitivity),
            max(50, hold_color_hsv[1] - saturation_sensitivity), # Min saturation
            max(50, hold_color_hsv[2] - value_sensitivity),   # Min value
        ]
    )
    upper_bound = np.array(
        [
            min(179, hold_color_hsv[0] + hue_sensitivity),
            255, # Max saturation
            255, # Max value
        ]
    )
    mask = cv2.inRange(hsv, lower_bound, upper_bound)

    # Blob Detection
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 100
    params.maxArea = 5000
    params.filterByCircularity = True
    params.minCircularity = 0.3  # Relaxed from 0.6
    params.filterByConvexity = True
    params.minConvexity = 0.5  # Relaxed from 0.8
    params.filterByInertia = True
    params.minInertiaRatio = 0.1  # Relaxed from 0.4
    detector = cv2.SimpleBlobDetector_create(params)

    # Detect blobs directly on the mask (for light holds on dark background)
    keypoints = detector.detect(mask)

    holds = [{"x": kp.pt[0], "y": kp.pt[1], "size": kp.size} for kp in keypoints]
    print(f"[Worker] Detected {len(holds)} holds.")
    return holds


async def analyze_climb(ctx, climb_id: int, file_key: str):
    """
    Background job triggered by ARQ.
    Downloads video, runs pose estimation, infers route color, detects holds,
    and updates the database.
    """
    print(f"[Worker] Starting analysis for Climb ID: {climb_id}")

    os.makedirs(TEMP_DIR, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(suffix=".mp4", dir=TEMP_DIR)
    os.close(fd)

    async with async_session_factory() as session:
        try:
            stmt = select(Climb).where(Climb.id == climb_id)
            result = await session.execute(stmt)
            climb = result.scalars().first()
            if not climb:
                print(f"[Worker] Climb {climb_id} not found.")
                return

            climb.status = ClimbStatus.PROCESSING
            await session.commit()

            if "http" in file_key:
                actual_file_key = file_key.split(f"/{S3_BUCKET_NAME}/")[-1]
            else:
                actual_file_key = file_key

            print(f"[Worker] Downloading S3 key '{actual_file_key}' to {tmp_path}...")
            async with await get_s3_client() as s3:
                await s3.download_file(S3_BUCKET_NAME, actual_file_key, tmp_path)
            print("[Worker] Download completed.")

            # --- Sequential CV Logic ---
            
            # 1. Run Pose Estimation
            print(f"[Worker] Running pose estimation...")
            pose_data = await asyncio.to_thread(run_pose_estimation, tmp_path)
            
            # 2. Infer Route Color from Pose
            print(f"[Worker] Inferring route color from pose...")
            inferred_color = await asyncio.to_thread(
                infer_route_color_from_video, tmp_path, pose_data
            )

            # 3. Detect Route Holds with Inferred Color
            route_data = []
            if inferred_color is not None:
                print(f"[Worker] Running route detection with inferred color...")
                route_data = await asyncio.to_thread(
                    run_route_detection, tmp_path, inferred_color
                )
            else:
                print("[Worker] Skipping route detection due to no inferred color.")

            # --- End CV Logic ---

            climb.analysis_results = {
                "pose_data": pose_data,
                "route_data": route_data,
            }
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
