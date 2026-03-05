// frontend/src/components/ResultViewer.tsx
import React, { useRef, useEffect } from "react";
import { type ClimbResponse } from "./UploadManager";

interface ResultViewerProps {
  climb: ClimbResponse;
}

export function ResultViewer({ climb }: ResultViewerProps) {
  const videoFileName = climb.video_url.split("/").pop();

  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const requestRef = useRef<number>();

  // Use the real pose data from the backend, default to empty array if undefined
  const poseData = climb.pose_data || [];

  const drawOverlay = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    // Only attempt to draw if we have elements and actual pose data
    if (video && canvas && poseData.length > 0) {
      if (
        canvas.width !== video.clientWidth ||
        canvas.height !== video.clientHeight
      ) {
        canvas.width = video.clientWidth;
        canvas.height = video.clientHeight;
      }

      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const currentTimeMs = video.currentTime * 1000;

        // Find the closest pose frame to the video's current time
        const currentFrame = poseData.reduce((prev, curr) =>
          Math.abs(curr.timestamp_ms - currentTimeMs) <
          Math.abs(prev.timestamp_ms - currentTimeMs)
            ? curr
            : prev,
        );

        // Render if the frame is within 100ms of the video time
        if (
          currentFrame &&
          Math.abs(currentFrame.timestamp_ms - currentTimeMs) < 100
        ) {
          ctx.fillStyle = "#ef4444"; // Tailwind Red-500

          currentFrame.keypoints.forEach((kp) => {
            // Check 'v' instead of 'visibility'
            if (kp.v && kp.v > 0.5) {
              const x = kp.x * canvas.width;
              const y = kp.y * canvas.height;

              ctx.beginPath();
              ctx.arc(x, y, 6, 0, 2 * Math.PI);
              ctx.fill();

              ctx.lineWidth = 2;
              ctx.strokeStyle = "white";
              ctx.stroke();
            }
          });
        }
      }
    }

    requestRef.current = requestAnimationFrame(drawOverlay);
  };

  useEffect(() => {
    const video = videoRef.current;

    const handlePlay = () => {
      requestRef.current = requestAnimationFrame(drawOverlay);
    };

    const handlePause = () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };

    const handleSeeked = () => {
      drawOverlay();
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };

    if (video) {
      video.addEventListener("play", handlePlay);
      video.addEventListener("pause", handlePause);
      video.addEventListener("seeked", handleSeeked);
    }

    return () => {
      if (video) {
        video.removeEventListener("play", handlePlay);
        video.removeEventListener("pause", handlePause);
        video.removeEventListener("seeked", handleSeeked);
      }
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [poseData]);

  return (
    <div className="flex flex-col w-full bg-gray-50 p-4 rounded-xl border border-gray-200">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-lg font-bold text-gray-800">
          Climb ID: #{climb.id}
        </h3>
        <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-md uppercase tracking-wider">
          {climb.status}
        </span>
      </div>

      <div className="relative w-full bg-black rounded-lg overflow-hidden shadow-sm border border-gray-300 flex justify-center">
        <video
          ref={videoRef}
          src={`/crux-videos/videos/${videoFileName}`}
          controls
          className="w-full h-auto aspect-video object-contain bg-black"
        />
        <canvas
          ref={canvasRef}
          className="absolute top-0 left-0 w-full h-full pointer-events-none"
        />
      </div>
    </div>
  );
}
