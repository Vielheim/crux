import pytest
import asyncio
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from app.worker import analyze_climb, run_pose_estimation
from app.models import Climb, ClimbStatus

# --- Test 1: The CV Logic (Unit Test) ---
# (This part was fine, but including for completeness)


def test_run_pose_estimation_success():
    """Test that pose estimation processes frames and returns data."""
    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)

    with patch("cv2.VideoCapture") as mock_cap_cls:
        mock_cap = mock_cap_cls.return_value
        mock_cap.isOpened.side_effect = [True, True, True, False]
        mock_cap.read.side_effect = [
            (True, dummy_frame),
            (True, dummy_frame),
            (True, dummy_frame),
            (False, None),
        ]
        mock_cap.get.return_value = 3.0

        with patch("mediapipe.solutions.pose.Pose") as mock_pose_cls:
            mock_pose_instance = mock_pose_cls.return_value
            mock_pose_instance.__enter__.return_value = mock_pose_instance

            mock_lm = MagicMock()
            mock_lm.x, mock_lm.y, mock_lm.z, mock_lm.visibility = 0.1, 0.2, 0.3, 0.9

            result_detected = MagicMock()
            result_detected.pose_landmarks.landmark = [mock_lm]
            result_empty = MagicMock()
            result_empty.pose_landmarks = None

            mock_pose_instance.process.side_effect = [
                result_detected,
                result_empty,
                result_detected,
            ]

            results = run_pose_estimation("dummy_path.mp4")

            assert len(results["pose_data"]) == 3
            assert results["pose_data"][0] is not None
            assert results["pose_data"][1] is None
            assert results["pose_data"][2] is not None
            assert results["fps"] == 3.0


def test_run_pose_estimation_integrity_failure():
    """Test that we raise ValueError if processed frames << expected frames."""
    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)

    with patch("cv2.VideoCapture") as mock_cap_cls:
        mock_cap = mock_cap_cls.return_value
        mock_cap.get.return_value = 100.0
        mock_cap.isOpened.side_effect = [True] * 11
        mock_cap.read.side_effect = [(True, dummy_frame)] * 10 + [(False, None)]

        with patch("mediapipe.solutions.pose.Pose") as mock_pose_cls:
            mock_pose_instance = mock_pose_cls.return_value
            mock_pose_instance.__enter__.return_value = mock_pose_instance
            mock_pose_instance.process.return_value = MagicMock(pose_landmarks=None)

            with pytest.raises(ValueError, match="Video analysis incomplete"):
                run_pose_estimation("dummy.mp4")


# --- Test 2: The Worker Job (Integration Test) ---


@pytest.mark.asyncio
async def test_analyze_climb_success(db_session):
    """
    Test the full flow with robust Session Patching.
    """
    # 1. Setup Data
    climb = Climb(
        user_id=1, video_url="s3://bucket/test.mp4", status=ClimbStatus.PENDING
    )
    db_session.add(climb)
    await db_session.commit()
    await db_session.refresh(climb)

    # 2. Mock S3
    mock_s3 = AsyncMock()
    mock_s3.download_file = AsyncMock(return_value=None)

    # The context manager returned by get_s3_client()
    mock_s3_ctx_manager = AsyncMock()
    mock_s3_ctx_manager.__aenter__.return_value = mock_s3
    mock_s3_ctx_manager.__aexit__.return_value = None

    # 3. Mock Session Factory
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__.return_value = db_session
    mock_session_cm.__aexit__.return_value = None
    mock_factory = MagicMock(return_value=mock_session_cm)

    # 4. Run Test
    # KEY FIX: new_callable=AsyncMock ensures get_s3_client() is a coroutine
    with patch(
        "app.worker.get_s3_client", new_callable=AsyncMock
    ) as mock_get_s3, patch(
        "app.worker.run_pose_estimation", return_value={"pose_data": [{"x": 1}], "fps": 30.0}
    ) as mock_cv, patch(
        "app.worker.async_session_factory", mock_factory
    ):

        # Configure the return value of our forced MagicMock
        mock_get_s3.return_value = mock_s3_ctx_manager

        await analyze_climb({}, climb.id, "test.mp4")

        await db_session.refresh(climb)

        assert climb.status == ClimbStatus.COMPLETED
        assert climb.analysis_results == {"pose_data": [{"x": 1}], "fps": 30.0}


@pytest.mark.asyncio
async def test_analyze_climb_failure_handling(db_session):
    """Test failure path with robust mocking."""

    climb = Climb(
        user_id=1, video_url="s3://bucket/fail.mp4", status=ClimbStatus.PENDING
    )
    db_session.add(climb)
    await db_session.commit()
    await db_session.refresh(climb)

    # Mock S3 to raise an error
    mock_s3_ctx_manager = AsyncMock()
    mock_s3_ctx_manager.__aenter__.side_effect = Exception("S3 Download Error")

    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__.return_value = db_session
    mock_session_cm.__aexit__.return_value = None
    mock_factory = MagicMock(return_value=mock_session_cm)

    # KEY FIX: new_callable=AsyncMock
    with patch(
        "app.worker.get_s3_client", new_callable=AsyncMock
    ) as mock_get_s3, patch("app.worker.async_session_factory", mock_factory):

        mock_get_s3.return_value = mock_s3_ctx_manager

        await analyze_climb({}, climb.id, "fail.mp4")

        await db_session.refresh(climb)

        assert climb.status == ClimbStatus.FAILED
        assert "S3 Download Error" in climb.analysis_results["error"]
