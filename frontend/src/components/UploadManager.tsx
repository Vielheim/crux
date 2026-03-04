// frontend/src/components/UploadManager.tsx
import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { UploadCloud, Video, Loader2, AlertCircle } from 'lucide-react';

// Make sure this matches your backend schema
export interface ClimbResponse {
  id: number;
  video_url: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
}

interface UploadManagerProps {
  onAnalysisComplete: (climb: ClimbResponse) => void;
}

export function UploadManager({ onAnalysisComplete }: UploadManagerProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeClimbId, setActiveClimbId] = useState<number | null>(null);

  // 1. Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', '1'); // Hardcoded until auth is built

      const response = await axios.post<ClimbResponse>('/api/upload-video', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    onSuccess: (data) => {
      setActiveClimbId(data.id);
    },
  });

  // 2. Polling Query
  const { data: climb, isError: isPollError } = useQuery({
    queryKey: ['climbStatus', activeClimbId],
    queryFn: async () => {
      const response = await axios.get<ClimbResponse>(`/api/climb/${activeClimbId}`);
      return response.data;
    },
    enabled: !!activeClimbId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'COMPLETED') {
        onAnalysisComplete(query.state.data);
        return false; // Stop polling
      }
      if (status === 'FAILED') return false; // Stop polling
      return 2000; // Poll every 2 seconds
    },
  });

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
      setActiveClimbId(null);
      uploadMutation.reset();
    }
  };

  const handleUpload = () => {
    if (selectedFile) uploadMutation.mutate(selectedFile);
  };

  const isUploading = uploadMutation.isPending;
  const isPolling = climb && (climb.status === 'PENDING' || climb.status === 'PROCESSING');

  // If we have a completed climb, this component shouldn't render its main UI
  if (climb?.status === 'COMPLETED') return null;

  return (
    <div className="w-full">
      {!activeClimbId && (
        <div className="flex flex-col items-center w-full">
          <label
            htmlFor="dropzone-file"
            className={`flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-xl cursor-pointer transition-colors duration-200 group
              ${isUploading ? 'border-gray-300 bg-gray-50' : 'border-indigo-300 bg-indigo-50/50 hover:bg-indigo-50'}`}
          >
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              {isUploading ? (
                <Loader2 className="w-12 h-12 text-indigo-500 mb-4 animate-spin" />
              ) : (
                <UploadCloud className="w-12 h-12 text-indigo-400 mb-4 group-hover:text-indigo-600 transition-colors" />
              )}
              <p className="mb-2 text-sm text-gray-600 font-medium">
                {isUploading ? 'Uploading video...' : <><span className="font-semibold text-indigo-600">Click to upload</span> or drag and drop</>}
              </p>
              {!isUploading && <p className="text-xs text-gray-500">MP4 or MOV (MAX. 100MB)</p>}
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
            <div className="mt-6 w-full p-4 bg-gray-50 rounded-lg border border-gray-200 flex items-center justify-between">
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
          
          {uploadMutation.isError && (
            <p className="mt-4 text-sm text-red-500 flex items-center justify-center">
              <AlertCircle className="w-4 h-4 mr-2" /> Upload failed. Check console.
            </p>
          )}
        </div>
      )}

      {activeClimbId && (isPolling || climb?.status === 'FAILED' || isPollError) && (
        <div className="flex flex-col items-center justify-center py-10">
          {isPolling && (
            <>
              <Loader2 className="w-16 h-16 text-indigo-500 mb-6 animate-spin" />
              <h3 className="text-xl font-bold text-gray-800">Analyzing your climb...</h3>
              <p className="text-gray-500 mt-2">Status: {climb?.status}</p>
            </>
          )}
          {(climb?.status === 'FAILED' || isPollError) && (
            <>
              <AlertCircle className="w-16 h-16 text-red-500 mb-6" />
              <h3 className="text-xl font-bold text-gray-800">Analysis Failed</h3>
              <p className="text-gray-500 mt-2">There was an error processing your video.</p>
              <button 
                onClick={() => { setSelectedFile(null); setActiveClimbId(null); }}
                className="mt-6 px-4 py-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 font-medium"
              >
                Try Again
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}