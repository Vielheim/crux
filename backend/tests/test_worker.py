import pytest
import asyncio
import cv2
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from app.worker import (
    analyze_climb,
    run_pose_estimation,
    infer_route_color_from_video,
    run_route_detection,
)
from app.models import Climb, ClimbStatus

# --- Unit Tests for CV Functions ---


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
            result_detected.pose_landmarks.landmark = [
                mock_lm
            ] * 34  # Full landmark set
            result_empty = MagicMock()
            result_empty.pose_landmarks = None

            mock_pose_instance.process.side_effect = [
                result_detected,
                result_empty,
                result_detected,
            ]

            pose_data, fps = run_pose_estimation("dummy_path.mp4")

            assert len(pose_data) == 3
            assert pose_data[0] is not None
            assert pose_data[1] is None
            assert pose_data[2] is not None
            assert len(pose_data[0]) == 34
            assert fps == 3.0


def test_infer_route_color_from_video():
    """
    Test the color inference from pose landmarks using a frame with actual color.
    """
    # Create a dummy frame with a dull background and a saturated hold color
    frame_h, frame_w = 100, 100
    # Dull gray in BGR
    dummy_frame = np.full((frame_h, frame_w, 3), (128, 128, 128), dtype=np.uint8)

    # Bright green in BGR, at the center where the landmark will be
    # Note: OpenCV uses BGR, but our function converts to HSV.
    # A bright green BGR becomes a highly saturated color in HSV.
    hold_color_bgr = (0, 255, 0)
    cx, cy, radius = 50, 50, 10
    cv2.rectangle(
        dummy_frame,
        (cx - radius, cy - radius),
        (cx + radius, cy + radius),
        hold_color_bgr,
        -1,
    )

    # Mock pose data with a landmark right in the middle of our green square
    mock_pose = [[{"x": cx, "y": cy, "z": 0, "v": 0.9}] * 34]

    with patch("cv2.VideoCapture") as mock_cap_cls:
        # Setup VideoCapture mock
        mock_cap = mock_cap_cls.return_value
        mock_cap.isOpened.return_value = True
        mock_cap.set.return_value = None
        mock_cap.read.return_value = (True, dummy_frame)
        mock_cap.release.return_value = None

        # We no longer need to mock KMeans, we're testing with "real" data.
        inferred_color_hsv = infer_route_color_from_video("dummy.mp4", mock_pose)

        assert inferred_color_hsv is not None

        # Convert the BGR hold color to HSV to get the approximate expected hue
        expected_hsv = cv2.cvtColor(np.uint8([[hold_color_bgr]]), cv2.COLOR_BGR2HSV)[0][
            0
        ]

        # The inferred hue should be very close to the actual hue of green (~60)
        assert abs(inferred_color_hsv[0] - expected_hsv[0]) < 5
        # The inferred saturation should be high (greater than the wall's)
        assert inferred_color_hsv[1] > 200


def test_run_route_detection():
    """Test the hold detection based on a given color."""
    dummy_frame = np.zeros((200, 200, 3), dtype=np.uint8)
    mock_color = np.array([120, 220, 220])  # A sample bright, saturated color

    # Mock keypoints that the blob detector should find
    mock_kp = MagicMock()
    mock_kp.pt = (50.0, 50.0)
    mock_kp.size = 20.0

    with patch("cv2.VideoCapture") as mock_cap_cls, patch(
        "cv2.SimpleBlobDetector_create"
    ) as mock_detector_cls:

        mock_cap = mock_cap_cls.return_value
        mock_cap.read.return_value = (True, dummy_frame)
        mock_cap.release.return_value = None

        mock_detector = mock_detector_cls.return_value
        mock_detector.detect.return_value = [mock_kp]

        holds = run_route_detection("dummy.mp4", mock_color)

        assert len(holds) == 1
        assert holds[0] == {"x": 50.0, "y": 50.0, "size": 20.0}
        # Check that the detector was called on an inverted mask
        mock_detector.detect.assert_called_once()


# --- Integration Test for the Worker Job ---


@pytest.mark.asyncio
async def test_analyze_climb_success_sequential(db_session):
    """
    Test the full success flow with the new sequential CV logic.
    """
    climb = Climb(
        user_id=1, video_url="s3://bucket/test.mp4", status=ClimbStatus.PENDING
    )
    db_session.add(climb)
    await db_session.commit()
    await db_session.refresh(climb)

    mock_s3 = AsyncMock()
    mock_s3_ctx_manager = AsyncMock(__aenter__=AsyncMock(return_value=mock_s3))

    mock_session_cm = AsyncMock(__aenter__=AsyncMock(return_value=db_session))
    mock_factory = MagicMock(return_value=mock_session_cm)

    # Mock data from our CV functions
    mock_pose_data = [{"pose_landmark": 1}]
    mock_video_fps = 30.0
    mock_inferred_color = np.array([100, 200, 200])
    mock_route_data = [{"x": 10, "y": 20, "size": 30}]

    with patch("app.worker.get_s3_client", return_value=mock_s3_ctx_manager), patch(
        "app.worker.async_session_factory", mock_factory
    ), patch(
        "app.worker.run_pose_estimation", return_value=(mock_pose_data, mock_video_fps)
    ) as mock_pose, patch(
        "app.worker.infer_route_color_from_video", return_value=mock_inferred_color
    ) as mock_infer, patch(
        "app.worker.run_route_detection", return_value=mock_route_data
    ) as mock_route:

        # Use a MagicMock to track call order
        manager = MagicMock()
        manager.attach_mock(mock_pose, "pose")
        manager.attach_mock(mock_infer, "infer")
        manager.attach_mock(mock_route, "route")

        await analyze_climb({}, climb.id, "test.mp4")

        await db_session.refresh(climb)

        # Assert correct status and results
        assert climb.status == ClimbStatus.COMPLETED
        assert climb.analysis_results["pose_data"] == mock_pose_data
        assert climb.analysis_results["route_data"] == mock_route_data

        # Assert CV functions were called in the correct order
        call_order = [name for name, _, _ in manager.mock_calls]
        assert call_order == ["pose", "infer", "route"]

        # Assert arguments were passed correctly
        mock_pose.assert_called_once()
        mock_infer.assert_called_once_with(mock_pose.call_args[0][0], mock_pose_data)
        mock_route.assert_called_once_with(
            mock_infer.call_args[0][0], mock_inferred_color
        )


@pytest.mark.asyncio
async def test_analyze_climb_no_color_inferred(db_session):
    """Test the flow where color inference fails but the job still completes."""
    climb = Climb(
        user_id=1, video_url="s3://bucket/test.mp4", status=ClimbStatus.PENDING
    )
    db_session.add(climb)
    await db_session.commit()
    await db_session.refresh(climb)

    mock_s3_ctx_manager = AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock()))
    mock_session_cm = AsyncMock(__aenter__=AsyncMock(return_value=db_session))
    mock_factory = MagicMock(return_value=mock_session_cm)

    mock_pose_data = [{"pose_landmark": 1}]

    with patch("app.worker.get_s3_client", return_value=mock_s3_ctx_manager), patch(
        "app.worker.async_session_factory", mock_factory
    ), patch("app.worker.run_pose_estimation", return_value=(mock_pose_data, 30.0)), patch(
        "app.worker.infer_route_color_from_video", return_value=None
    ) as mock_infer, patch(
        "app.worker.run_route_detection"
    ) as mock_route:

        await analyze_climb({}, climb.id, "test.mp4")

        await db_session.refresh(climb)

        assert climb.status == ClimbStatus.COMPLETED
        assert climb.analysis_results["pose_data"] == mock_pose_data
        assert climb.analysis_results["route_data"] == []  # Should be empty
        mock_infer.assert_called_once()
        mock_route.assert_not_called()  # Crucially, detection should be skipped


@pytest.mark.asyncio
async def test_analyze_climb_cv_exception(db_session):
    """Test that an exception in a CV function leads to a FAILED status."""
    climb = Climb(
        user_id=1, video_url="s3://bucket/fail.mp4", status=ClimbStatus.PENDING
    )
    db_session.add(climb)
    await db_session.commit()
    await db_session.refresh(climb)

    mock_s3_ctx_manager = AsyncMock(__aenter__=AsyncMock(return_value=AsyncMock()))
    mock_session_cm = AsyncMock(__aenter__=AsyncMock(return_value=db_session))
    mock_factory = MagicMock(return_value=mock_session_cm)

    with patch("app.worker.get_s3_client", return_value=mock_s3_ctx_manager), patch(
        "app.worker.async_session_factory", mock_factory
    ), patch("app.worker.run_pose_estimation", side_effect=ValueError("CV Error")):

        await analyze_climb({}, climb.id, "fail.mp4")

        await db_session.refresh(climb)

        assert climb.status == ClimbStatus.FAILED
        assert "CV Error" in climb.analysis_results["error"]
