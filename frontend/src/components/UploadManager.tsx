// frontend/src/components/UploadManager.tsx
import React, { useState, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  UploadCloud,
  Video,
  Loader2,
  AlertCircle,
  Terminal,
} from "lucide-react";

export interface Keypoint {
  x: number;
  y: number;
  z: number;
  v: number;
}

export interface AnalysisResults {
  pose_data?: Keypoint[][]; // An array of frames, each containing an array of Keypoints
  error?: string;
}

export interface ClimbResponse {
  id: number;
  video_url: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  analysis_results?: AnalysisResults; // The root dictionary
}

interface UploadManagerProps {
  onAnalysisComplete: (climb: ClimbResponse) => void;
}

export function UploadManager({ onAnalysisComplete }: UploadManagerProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeClimbId, setActiveClimbId] = useState<number | null>(null);
  const [debugLogs, setDebugLogs] = useState<string[]>([]);

  const addLog = (message: string, data?: any) => {
    const timestamp = new Date().toLocaleTimeString();
    const logStr = data
      ? `${message}: ${JSON.stringify(data, null, 2)}`
      : message;
    setDebugLogs((prev) => [`[${timestamp}] ${logStr}`, ...prev]);
  };

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      addLog("Initiating upload...");
      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", "1");

      const response = await axios.post<ClimbResponse>(
        "/api/upload-video",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        },
      );
      return response.data;
    },
    onSuccess: (data) => {
      addLog("Upload successful! Received Climb ID", data.id);
      setActiveClimbId(data.id);
    },
    onError: (error) => {
      if (axios.isAxiosError(error)) {
        addLog(
          `Upload Failed (${error.response?.status || "Network Error"})`,
          error.response?.data || error.message,
        );
      } else {
        addLog("Unknown Upload Error", (error as Error).message);
      }
    },
  });

  const {
    data: climb,
    isError: isPollError,
    error: pollError,
  } = useQuery({
    queryKey: ["climbStatus", activeClimbId],
    queryFn: async () => {
      addLog(`Polling status for Climb ID: ${activeClimbId}...`);
      const response = await axios.get<ClimbResponse>(
        `/api/climb/${activeClimbId}`,
      );
      return response.data;
    },
    enabled: !!activeClimbId,
    // Only return the interval time or false to stop. No side effects here!
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "COMPLETED" || status === "FAILED") {
        return false;
      }
      return 2000;
    },
  });

  // Handle successful completion side-effects exactly once
  useEffect(() => {
    if (climb?.status === "COMPLETED" && activeClimbId) {
      addLog("Analysis COMPLETED!");
      onAnalysisComplete(climb);

      const timeoutId = setTimeout(() => {
        setActiveClimbId(null);
        setSelectedFile(null);
        uploadMutation.reset();
      }, 2000);

      return () => clearTimeout(timeoutId);
    }

    if (climb?.status === "FAILED") {
      addLog("Analysis FAILED on the backend.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [climb?.status]); // Deliberately only depending on status to prevent infinite re-renders

  useEffect(() => {
    if (isPollError && pollError) {
      addLog(
        "Polling Error",
        axios.isAxiosError(pollError)
          ? pollError.response?.data || pollError.message
          : pollError.message,
      );
    }
  }, [isPollError, pollError]);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
      setActiveClimbId(null);
      setDebugLogs([]);
      uploadMutation.reset();
      addLog(`Selected file: ${event.target.files[0].name}`);
    }
  };

  const handleUpload = () => {
    if (selectedFile) uploadMutation.mutate(selectedFile);
  };

  const isUploading = uploadMutation.isPending;
  const isPolling =
    climb && (climb.status === "PENDING" || climb.status === "PROCESSING");
  const isCompleted = climb?.status === "COMPLETED";

  return (
    <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
      {/* LEFT SIDE: Upload / Status UI */}
      <div className="flex flex-col w-full">
        {!activeClimbId && (
          <div className="flex flex-col items-center w-full">
            <label
              htmlFor="dropzone-file"
              className={`flex flex-col items-center justify-center w-full h-72 border-2 border-dashed rounded-xl cursor-pointer transition-colors duration-200 group
                ${isUploading ? "border-gray-300 bg-gray-50" : "border-indigo-300 bg-indigo-50/50 hover:bg-indigo-50"}`}
            >
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                {isUploading ? (
                  <Loader2 className="w-12 h-12 text-indigo-500 mb-4 animate-spin" />
                ) : (
                  <UploadCloud className="w-12 h-12 text-indigo-400 mb-4 group-hover:text-indigo-600 transition-colors" />
                )}
                <p className="mb-2 text-sm text-gray-600 font-medium">
                  {isUploading ? (
                    "Uploading video..."
                  ) : (
                    <>
                      <span className="font-semibold text-indigo-600">
                        Click to upload
                      </span>{" "}
                      or drag and drop
                    </>
                  )}
                </p>
                {!isUploading && (
                  <p className="text-xs text-gray-500">
                    MP4 or MOV (MAX. 500MB)
                  </p>
                )}
              </div>
              <input
                id="dropzone-file"
                type="file"
                className="hidden"
                accept="video/mp4,video/quicktime"
                onChange={handleFileChange}
                disabled={isUploading}
              />
            </label>

            {selectedFile && !isUploading && (
              <div className="mt-4 w-full p-4 bg-gray-50 rounded-lg border border-gray-200 flex items-center justify-between">
                <div className="flex items-center space-x-3 overflow-hidden">
                  <Video className="w-6 h-6 text-indigo-500 flex-shrink-0" />
                  <span className="text-sm font-medium text-gray-700 truncate max-w-[200px]">
                    {selectedFile.name}
                  </span>
                </div>
                <button
                  onClick={handleUpload}
                  className="px-5 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
                >
                  Analyze
                </button>
              </div>
            )}
          </div>
        )}

        {activeClimbId && (
          <div className="flex flex-col items-center justify-center h-72 bg-gray-50 border border-gray-200 rounded-xl">
            {isPolling && (
              <>
                <Loader2 className="w-12 h-12 text-indigo-500 mb-4 animate-spin" />
                <h3 className="text-lg font-bold text-gray-800">
                  Analyzing climb...
                </h3>
                <p className="text-gray-500 mt-1">Status: {climb?.status}</p>
              </>
            )}

            {isCompleted && (
              <>
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
                  <div
                    className="w-6 h-6 border-4 border-green-500 border-t-transparent rounded-full animate-spin"
                    style={{ animationDuration: "3s" }}
                  />
                </div>
                <h3 className="text-lg font-bold text-gray-800">Complete!</h3>
                <p className="text-gray-500 mt-1">Resetting view...</p>
              </>
            )}

            {(climb?.status === "FAILED" ||
              uploadMutation.isError ||
              isPollError) && (
              <>
                <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
                <h3 className="text-lg font-bold text-gray-800">
                  Process Failed
                </h3>
                <button
                  onClick={() => {
                    setSelectedFile(null);
                    setActiveClimbId(null);
                    setDebugLogs([]);
                  }}
                  className="mt-4 px-4 py-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 font-medium text-sm"
                >
                  Start Over
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* RIGHT SIDE: Debug Logs Section */}
      <div className="w-full flex flex-col bg-slate-900 rounded-xl p-4 shadow-inner border border-slate-700 h-72">
        <div className="flex items-center space-x-2 mb-3 shrink-0">
          <Terminal className="w-5 h-5 text-green-400" />
          <h4 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
            Debug Logs
          </h4>
        </div>

        <div className="flex-1 overflow-y-auto bg-slate-950 p-3 rounded font-mono text-xs text-green-400 border border-slate-800 space-y-1">
          {debugLogs.length === 0 ? (
            <p className="text-slate-600 italic">No network activity yet...</p>
          ) : (
            debugLogs.map((log, index) => (
              <div
                key={index}
                className="whitespace-pre-wrap break-words border-b border-slate-800/50 pb-1"
              >
                {log}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
