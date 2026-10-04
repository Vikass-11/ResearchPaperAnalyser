import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { papersApi } from "../../../api";
import { LoadingState } from "../../common/LoadingState";
import { ErrorState } from "../../common/ErrorState";
import { PipelineProgress } from "../PipelineProgress";
import { FileText, Network, BarChart, Search } from "lucide-react";

export function PaperOverview() {
  const { paper, pipelineStatus } = useOutletContext();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!paper) return;
    
    const fetchSummary = async () => {
      try {
        const data = await papersApi.getResearchSummary(paper.id);
        setSummary(data);
        setError(null);
      } catch (err) {
        setError(err.message || "Failed to load research summary.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchSummary();
  }, [paper]);

  if (loading) return <LoadingState message="Loading overview..." />;
  if (error) return <ErrorState title="Overview Unavailable" message={error} />;

  // Display fields that exist on summary
  const statCards = [
    { label: "Related Papers", value: summary?.related_papers_count ?? "-", icon: Network, color: "text-blue-500", bg: "bg-blue-50" },
    { label: "Analyzed Papers", value: summary?.analyzed_papers_count ?? "-", icon: BarChart, color: "text-brand-500", bg: "bg-brand-50" },
    { label: "Research Gaps", value: summary?.research_gaps_count ?? "-", icon: Search, color: "text-amber-500", bg: "bg-amber-50" },
    { label: "Recent Works", value: summary?.recent_research_count ?? "-", icon: FileText, color: "text-emerald-500", bg: "bg-emerald-50" },
  ];

  return (
    <div className="flex flex-col gap-8 animate-fade-in">
      <PipelineProgress statusData={pipelineStatus} />
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((stat, i) => (
          <div key={i} className="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col justify-between">
            <div className={`p-3 w-fit rounded-xl ${stat.bg} ${stat.color} mb-4`}>
              <stat.icon className="w-5 h-5" />
            </div>
            <div>
              <p className="text-3xl font-bold text-slate-900">{stat.value}</p>
              <p className="text-sm font-medium text-slate-500 mt-1">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-xl font-bold text-slate-900 mb-6">Paper Abstract</h2>
        {paper.abstract ? (
          <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed">
            {paper.abstract}
          </div>
        ) : (
          <p className="text-slate-500 italic">No abstract available for this paper.</p>
        )}
      </div>
      
      {/* Basic AI Summary content if available directly on paper */}
      {paper.summary && (
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
          <h2 className="text-xl font-bold text-slate-900 mb-6">AI Research Summary</h2>
          <div className="prose prose-slate max-w-none text-slate-700 leading-relaxed">
            {paper.summary}
          </div>
        </div>
      )}
    </div>
  );
}
