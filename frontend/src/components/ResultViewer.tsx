// frontend/src/components/ResultViewer.tsx
import React, { useRef, useEffect } from "react";
import { type ClimbResponse } from "./UploadManager";

interface ResultViewerProps {
  climb: ClimbResponse;
}

export function ResultViewer({ climb }: ResultViewerProps) {
  const videoFileName = climb.video_url.split("/").pop();

  const containerRef = useRef<HTMLDivElement>(null); // NEW: Ref for the wrapper
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const requestRef = useRef<number>();

  const poseData = climb.analysis_results?.pose_data || [];

  // NEW: Function to toggle fullscreen on the container, not just the video
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

        const fps = 30;
        const frameIndex = Math.floor(video.currentTime * fps);

        if (frameIndex < poseData.length) {
          const currentFrame = poseData[frameIndex];

          if (currentFrame) {
            ctx.fillStyle = "#ef4444";

            currentFrame.forEach((kp) => {
              if (kp && kp.v > 0.5) {
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
    }

    requestRef.current = requestAnimationFrame(drawOverlay);
  };

  useEffect(() => {
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
          {/* NEW: Custom Fullscreen Button */}
          <button
            onClick={toggleFullScreen}
            className="px-3 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-medium rounded transition-colors"
          >
            Fullscreen
          </button>
        </div>
      </div>

      {/* NEW: Added double-click to fullscreen, and attached containerRef */}
      <div
        ref={containerRef}
        onDoubleClick={toggleFullScreen}
        className="relative w-full aspect-video bg-black rounded-lg overflow-hidden shadow-sm border border-gray-300"
      >
        <video
          ref={videoRef}
          src={`/crux-videos/videos/${videoFileName}`}
          controls
          controlsList="nofullscreen" // NEW: Hides the native fullscreen button
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
