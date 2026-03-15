// frontend/src/components/ResultViewer.tsx

import React, { useRef, useEffect } from "react";
// Import React Query hooks and axios
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { type ClimbResponse } from "./UploadManager";

interface ResultViewerProps {
  climb: ClimbResponse;
}

const POSE_CONNECTIONS = [
  // ... (Keep existing POSE_CONNECTIONS exactly as is) ...
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

export function ResultViewer({ climb }: ResultViewerProps) {
  const videoFileName = climb.video_url.split("/").pop();

  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const requestRef = useRef<number>();

  const poseData = climb.analysis_results?.pose_data || [];
  const fps = climb.analysis_results?.fps || 30;
  const timestamps = climb.analysis_results?.timestamps;

  // --- NEW: Query Client and Delete Mutation ---
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: async () => {
      await axios.delete(`/api/climb/${climb.id}`);
    },
    onSuccess: () => {
      // Instantly remove the deleted climb from the UI
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
  // -------------------------------------------

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen().catch((err) => {
        console.error(`Error attempting to enable fullscreen: ${err.message}`);
      });
    } else {
      document.exitFullscreen();
    }
  };

  const drawOverlay = () => {
    // ... (Keep existing drawOverlay logic exactly as is) ...
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas && poseData.length > 0) {
      if (
        video.videoWidth > 0 &&
        (canvas.width !== video.videoWidth ||
          canvas.height !== video.videoHeight)
      ) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
      }
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        let frameIndex = 0;
        if (timestamps && timestamps.length > 0) {
          let low = 0;
          let high = timestamps.length - 1;
          const target = video.currentTime;
          while (low <= high) {
            const mid = Math.floor((low + high) / 2);
            if (timestamps[mid] < target) {
              low = mid + 1;
            } else if (timestamps[mid] > target) {
              high = mid - 1;
            } else {
              low = mid;
              break;
            }
          }
          frameIndex = low;
          if (frameIndex >= timestamps.length) frameIndex = timestamps.length - 1;
          if (frameIndex > 0 && target - timestamps[frameIndex - 1] < timestamps[frameIndex] - target) {
            frameIndex = frameIndex - 1;
          }
        } else {
          frameIndex = Math.floor(video.currentTime * fps);
        }

        if (frameIndex < poseData.length) {
          const currentFrame = poseData[frameIndex];
          if (currentFrame) {
            ctx.lineWidth = 3;
            ctx.strokeStyle = "rgba(255, 255, 255, 0.8)";
            POSE_CONNECTIONS.forEach(([i, j]) => {
              const kp1 = currentFrame[i];
              const kp2 = currentFrame[j];
              if (kp1 && kp2 && kp1.v > 0.5 && kp2.v > 0.5) {
                ctx.beginPath();
                ctx.moveTo(kp1.x * canvas.width, kp1.y * canvas.height);
                ctx.lineTo(kp2.x * canvas.width, kp2.y * canvas.height);
                ctx.stroke();
              }
            });
            ctx.fillStyle = "#ef4444";
            currentFrame.forEach((kp, index) => {
              if (index >= 1 && index <= 10) return;
              if (kp && kp.v > 0.5) {
                const x = kp.x * canvas.width;
                const y = kp.y * canvas.height;
                ctx.beginPath();
                ctx.arc(x, y, 5, 0, 2 * Math.PI);
                ctx.fill();
                ctx.lineWidth = 2;
                ctx.strokeStyle = "white";
                ctx.stroke();
              }
            });
          }
        }
      }
    }
    requestRef.current = requestAnimationFrame(drawOverlay);
  };

  useEffect(() => {
    // ... (Keep existing useEffect exactly as is) ...
    const video = videoRef.current;
    const handlePlay = () =>
      (requestRef.current = requestAnimationFrame(drawOverlay));
    const handlePause = () =>
      requestRef.current && cancelAnimationFrame(requestRef.current);
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
        <div className="flex items-center gap-3">
          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-md uppercase tracking-wider">
            {climb.status}
          </span>
          <button
            onClick={toggleFullScreen}
            className="px-3 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-medium rounded transition-colors"
          >
            Fullscreen
          </button>

          {/* --- NEW: Delete Button --- */}
          <button
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
            className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-sm font-medium rounded transition-colors disabled:opacity-50"
          >
            {deleteMutation.isPending ? "..." : "Delete"}
          </button>
          {/* --------------------------- */}
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
