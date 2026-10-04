import { CheckCircle2, Loader2, Circle, AlertCircle } from "lucide-react";

export function PipelineProgress({ statusData }) {
  if (!statusData) return null;

  const steps = [
    { key: 'extracted_metadata', label: 'Paper Processed' },
    { key: 'generated_profile', label: 'Research Profile' },
    { key: 'discovered_related', label: 'Related Papers' },
    { key: 'ranked_papers', label: 'Relevance Ranking' },
    { key: 'analyzed_literature', label: 'Literature Analysis' },
    { key: 'synthesized_survey', label: 'Literature Survey' },
    { key: 'detected_gaps', label: 'Research Gaps' },
    { key: 'discovered_recent', label: 'Recent Research' },
  ];

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
      <h3 className="text-lg font-semibold text-slate-800 mb-4">Pipeline Status</h3>
      
      {statusData.status === "ERROR" && (
        <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-xl flex items-start gap-3 border border-red-100">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Analysis Failed</p>
            <p className="text-sm mt-1">{statusData.error_message || "An unknown error occurred during pipeline execution."}</p>
          </div>
        </div>
      )}

      {statusData.status === "PROCESSING" && (
        <div className="mb-4 p-4 bg-blue-50 text-blue-700 rounded-xl flex items-center gap-3 border border-blue-100">
          <Loader2 className="w-5 h-5 animate-spin flex-shrink-0" />
          <p className="text-sm font-medium">Research analysis is currently in progress...</p>
        </div>
      )}
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {steps.map((step) => {
          const isComplete = statusData.stages && statusData.stages[step.key];
          const isError = statusData.status === "ERROR";
          const isPending = !isComplete && !isError;
          
          return (
            <div key={step.key} className={`flex items-center gap-3 p-3 rounded-lg border ${
              isComplete ? 'bg-emerald-50/50 border-emerald-100 text-emerald-700' : 
              isError ? 'bg-slate-50 border-slate-200 text-slate-400 opacity-60' :
              'bg-white border-slate-200 text-slate-500'
            }`}>
              {isComplete ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              ) : isPending && statusData.status === "PROCESSING" ? (
                <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
              ) : (
                <Circle className="w-5 h-5 text-slate-300" />
              )}
              <span className="text-sm font-medium">{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
