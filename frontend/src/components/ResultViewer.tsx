// frontend/src/components/ResultViewer.tsx
import { type ClimbResponse } from "./UploadManager";

interface ResultViewerProps {
  climb: ClimbResponse;
}

export function ResultViewer({ climb }: ResultViewerProps) {
  // Extract filename from URL to use with our Nginx proxy
  const videoFileName = climb.video_url.split("/").pop();

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

      <div className="w-full relative bg-black rounded-lg overflow-hidden shadow-sm border border-gray-300">
        {/* The canvas overlay will go here in the next step */}
        <video
          src={`/crux-videos/${videoFileName}`}
          controls
          className="w-full h-auto aspect-video object-contain bg-black"
        />
      </div>
    </div>
  );
}
