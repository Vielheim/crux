// frontend/src/App.tsx
import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { UploadManager, type ClimbResponse } from "./components/UploadManager";
import { ResultViewer } from "./components/ResultViewer";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
});

function CruxDashboard() {
  // Store a list of completed climbs for the current session
  const [completedClimbs, setCompletedClimbs] = useState<ClimbResponse[]>([]);

  const handleAnalysisComplete = (climb: ClimbResponse) => {
    setCompletedClimbs((prev) => [climb, ...prev]);
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl w-full space-y-8 text-center mb-8">
        <h1 className="text-4xl font-extrabold text-indigo-600 tracking-tight">
          Crux Analysis
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          Upload your climb for AI-powered pose and route analysis.
        </p>
      </div>

      <div className="max-w-6xl w-full flex flex-col space-y-8">
        {/* Top Section: Upload Component (Left) & Debug Logs (Right) */}
        <div className="bg-white shadow-xl rounded-2xl p-6 sm:p-10 border border-gray-100">
          <UploadManager onAnalysisComplete={handleAnalysisComplete} />
        </div>

        {/* Bottom Section: List of uploaded/analyzed videos */}
        {completedClimbs.length > 0 && (
          <div className="bg-white shadow-xl rounded-2xl p-6 sm:p-10 border border-gray-100">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 pb-4 border-b border-gray-100">
              Recent Analysis Results
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {completedClimbs.map((climb) => (
                <ResultViewer key={climb.id} climb={climb} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <CruxDashboard />
    </QueryClientProvider>
  );
}
