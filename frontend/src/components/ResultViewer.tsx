// frontend/src/components/ResultViewer.tsx
import { CheckCircle } from "lucide-react";
import { type ClimbResponse } from "./UploadManager";

interface ResultViewerProps {
  climb: ClimbResponse;
  onReset: () => void;
}

export function ResultViewer({ climb, onReset }: ResultViewerProps) {
  // Extract filename from URL to use with our Nginx proxy
  const videoFileName = climb.video_url.split("/").pop();

  return (
    <div className="flex flex-col items-center w-full py-6">
      <CheckCircle className="w-16 h-16 text-green-500 mb-4" />
      <h3 className="text-2xl font-bold text-gray-800">Analysis Complete!</h3>

      <div className="w-full mt-6 relative bg-black rounded-xl overflow-hidden shadow-lg border border-gray-200">
        {/* We will add a <canvas> here in the next step! */}
        <video
          src={`/crux-videos/${videoFileName}`}
          controls
          className="w-full h-auto max-h-[600px] object-contain"
        />
      </div>

      <button
        onClick={onReset}
        className="mt-8 px-6 py-3 text-indigo-600 bg-indigo-50 rounded-lg hover:bg-indigo-100 font-medium transition-colors"
      >
        Analyze Another Climb
      </button>
    </div>
  );
}
