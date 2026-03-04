// frontend/src/App.tsx
import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { UploadManager, type ClimbResponse } from "./components/UploadManager";
import { ResultViewer } from "./components/ResultViewer";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
});

function CruxDashboard() {
  const [completedClimb, setCompletedClimb] = useState<ClimbResponse | null>(
    null,
  );

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl w-full space-y-8 text-center mb-8">
        <h1 className="text-4xl font-extrabold text-indigo-600 tracking-tight">
          Crux Analysis
        </h1>
        <p className="mt-2 text-lg text-gray-600">
          Upload your climb for AI-powered pose and route analysis.
        </p>
      </div>

      <div className="max-w-2xl w-full bg-white shadow-xl rounded-2xl p-6 sm:p-10 border border-gray-100">
        {!completedClimb ? (
          <UploadManager
            onAnalysisComplete={(climb) => setCompletedClimb(climb)}
          />
        ) : (
          <ResultViewer
            climb={completedClimb}
            onReset={() => setCompletedClimb(null)}
          />
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
