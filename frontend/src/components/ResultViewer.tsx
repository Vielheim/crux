// frontend/src/components/ResultViewer.tsx

import React, { useRef, useEffect, useCallback } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { type ClimbResponse } from "./UploadManager";

interface ResultViewerProps {
  climb: ClimbResponse;
}

// Landmark connections for drawing the skeleton
const POSE_CONNECTIONS = [
  [11, 12],
  [11, 23],
  [12, 24],
  [23, 24],
  [11, 13],
  [13, 15],
  [15, 17],
  [15, 19],
  [15, 21],
  [12, 14],
  [14, 16],
  [16, 18],
  [16, 20],
  [16, 22],
  [23, 25],
  [25, 27],
  [27, 29],
  [27, 31],
  [29, 31],
  [24, 26],
  [26, 28],
  [28, 30],
  [28, 32],
  [30, 32],
  [0, 11],
  [0, 12],
];

// --- Drawing Functions ---

function drawHolds(
  ctx: CanvasRenderingContext2D,
  holds: { x: number; y: number; size: number }[],
) {
  if (!holds || holds.length === 0) return;

  ctx.fillStyle = "rgba(74, 222, 128, 0.5)"; // Semi-transparent green
  ctx.strokeStyle = "rgba(34, 197, 94, 1)"; // Solid green
  ctx.lineWidth = 2;

  holds.forEach((hold) => {
    ctx.beginPath();
    // Use the 'size' from the blob detector for the radius
    ctx.arc(hold.x, hold.y, hold.size / 2, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();
  });
}

function drawPose(
  ctx: CanvasRenderingContext2D,
  poseFrame: { x: number; y: number; v: number }[],
) {
  if (!poseFrame) return;

  // Draw connections
  ctx.lineWidth = 3;
  ctx.strokeStyle = "rgba(255, 255, 255, 0.8)";
  POSE_CONNECTIONS.forEach(([i, j]) => {
    const kp1 = poseFrame[i];
    const kp2 = poseFrame[j];
    if (kp1 && kp2 && kp1.v > 0.5 && kp2.v > 0.5) {
      ctx.beginPath();
      ctx.moveTo(kp1.x, kp1.y);
      ctx.lineTo(kp2.x, kp2.y);
      ctx.stroke();
    }
  });

  // Draw keypoints
  ctx.fillStyle = "#ef4444"; // Red
  poseFrame.forEach((kp, index) => {
    // Skip the face keypoints for a cleaner look
    if (index >= 1 && index <= 10) return;

    if (kp && kp.v > 0.5) {
      ctx.beginPath();
      ctx.arc(kp.x, kp.y, 5, 0, 2 * Math.PI);
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = "white";
      ctx.stroke();
    }
  });
}

// --- Component ---

export function ResultViewer({ climb }: ResultViewerProps) {
  const videoFileName = climb.video_url.split("/").pop();

  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const requestRef = useRef<number>();

  const poseData = climb.analysis_results?.pose_data || [];
  const routeData = climb.analysis_results?.route_data || [];

  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: async () => {
      await axios.delete(`/api/climb/${climb.id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["climbs"] });
    },
    onError: (error) => {
      console.error("Failed to delete climb", error);
      alert("Failed to delete video. Check console for details.");
    },
  });

  const handleDelete = () => {
    if (
      window.confirm(
        "Are you sure you want to delete this climb? This cannot be undone.",
      )
    ) {
      deleteMutation.mutate();
    }
  };

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen().catch((err) => {
        console.error(`Error attempting to enable fullscreen: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  };

  const drawOverlay = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    // Ensure canvas is the same size as the video to prevent distortion
    if (
      video.videoWidth > 0 &&
      (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight)
    ) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const { videoWidth, videoHeight } = video;
    const { clientWidth: containerWidth, clientHeight: containerHeight } = canvas;

    if (!videoWidth || !videoHeight || !containerWidth || !containerHeight) {
      // Don't draw yet if video or canvas dimensions are not available
      return;
    }

    const videoAspectRatio = videoWidth / videoHeight;
    const containerAspectRatio = containerWidth / containerHeight;

    let scale = 1;
    let offsetX = 0;
    let offsetY = 0;

    if (videoAspectRatio > containerAspectRatio) {
      scale = containerWidth / videoWidth;
      offsetY = (containerHeight - videoHeight * scale) / 2;
    } else {
      scale = containerHeight / videoHeight;
      offsetX = (containerWidth - videoWidth * scale) / 2;
    }

    ctx.save();
    ctx.translate(offsetX, offsetY);
    ctx.scale(scale, scale);

    drawHolds(ctx, routeData);

    const fps = 30;
    const frameIndex = Math.floor(video.currentTime * fps);
    if (frameIndex < poseData.length) {
      drawPose(ctx, poseData[frameIndex]);
    }

    ctx.restore();

    requestRef.current = requestAnimationFrame(drawOverlay);
  }, [poseData, routeData]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handlePlay = () => {
      requestRef.current = requestAnimationFrame(drawOverlay);
    };
    const handlePause = () => {
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
    const handleSeeked = () => {
      // Redraw once after seeking
      drawOverlay();
      // Cancel any pending animation frame to avoid duplicate loops
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };

    video.addEventListener("play", handlePlay);
    video.addEventListener("pause", handlePause);
    video.addEventListener("seeked", handleSeeked);

    // Draw initial frame when video metadata is loaded
    video.addEventListener("loadedmetadata", () => {
      drawOverlay();
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    });

    return () => {
      video.removeEventListener("play", handlePlay);
      video.removeEventListener("pause", handlePause);
      video.removeEventListener("seeked", handleSeeked);
      if (requestRef.current) {
        cancelAnimationFrame(requestRef.current);
      }
    };
  }, [drawOverlay]);

  return (
    <div className="flex flex-col w-full bg-gray-50 p-4 rounded-xl border border-gray-200">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-lg font-bold text-gray-800">
          Climb ID: #{climb.id}
        </h3>
        <div className="flex items-center gap-3">
          <span
            className={`px-2 py-1 text-xs font-bold rounded-md uppercase tracking-wider ${
              climb.status === "COMPLETED"
                ? "bg-green-100 text-green-700"
                : "bg-yellow-100 text-yellow-700"
            }`}
          >
            {climb.status}
          </span>
          <button
            onClick={toggleFullScreen}
            className="px-3 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-medium rounded transition-colors"
          >
            Fullscreen
          </button>
          <button
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-sm font-medium rounded transition-colors disabled:opacity-50"
          >
            {deleteMutation.isPending ? "..." : "Delete"}
          </button>
        </div>
      </div>

      <div
        ref={containerRef}
        onDoubleClick={toggleFullScreen}
        className="relative w-full aspect-video bg-black rounded-lg overflow-hidden shadow-sm border border-gray-300"
      >
        <video
          ref={videoRef}
          src={`/crux-videos/videos/${videoFileName}`}
          controls
          controlsList="nofullscreen"
          crossOrigin="anonymous" // Required for canvas to access video frames from a different origin (Minio)
          className="absolute top-0 left-0 w-full h-full object-contain"
        />
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 w-full h-full object-contain pointer-events-none"
        />
      </div>

      <p className="text-xs text-gray-500 mt-2 text-center">
        Tip: Double-click the video to toggle fullscreen.
      </p>
    </div>
  );
}
