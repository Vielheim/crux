// frontend/src/App.tsx
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import axios from "axios";
import { UploadManager, type ClimbResponse } from "./components/UploadManager";
import { ResultViewer } from "./components/ResultViewer";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
});

function CruxDashboard() {
  const qc = useQueryClient();

  // Fetch all existing climbs for the user
  const { data: climbs = [], isLoading } = useQuery({
    queryKey: ["climbs"],
    queryFn: async () => {
      // TODO: Update this URL to match your exact backend test endpoint!
      const response = await axios.get<ClimbResponse[]>("/api/climbs/1");

      // Sort so the newest videos (highest ID) show up first
      return response.data.sort((a, b) => b.id - a.id);
    },
  });

  const handleAnalysisComplete = (climb: ClimbResponse) => {
    // Instead of manually managing state, we tell React Query the data is stale.
    // This will instantly trigger a background refetch of all climbs!
    qc.invalidateQueries({ queryKey: ["climbs"] });
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
        {(climbs.length > 0 || isLoading) && (
          <div className="bg-white shadow-xl rounded-2xl p-6 sm:p-10 border border-gray-100">
            <h2 className="text-2xl font-bold text-gray-800 mb-6 pb-4 border-b border-gray-100">
              Recent Analysis Results
            </h2>

            {isLoading ? (
              <div className="w-full flex justify-center py-8">
                <p className="text-gray-500 italic animate-pulse">
                  Loading past climbs...
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {climbs.map((climb) => (
                  <ResultViewer key={climb.id} climb={climb} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Wrapper component to provide the QueryClient context
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <CruxDashboard />
    </QueryClientProvider>
  );
}
