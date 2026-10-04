import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { literatureApi } from "../../../api";
import { LoadingState } from "../../common/LoadingState";
import { ErrorState } from "../../common/ErrorState";
import { EmptyState } from "../../common/EmptyState";
import { ExternalLink, CalendarDays, Zap } from "lucide-react";
import { Badge } from "../../common/Badge";

export function RecentResearch() {
  const { paper } = useOutletContext();
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!paper) return;
    
    const fetchRecent = async () => {
      try {
        const data = await literatureApi.getRecentResearch(paper.id, 1, 50);
        setRecent(data.recent_research || data.papers || data.items || []);
        setError(null);
      } catch (err) {
        if (err.status === 404) {
           setRecent([]);
        } else {
           setError(err.message || "Failed to load recent research.");
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchRecent();
  }, [paper]);

  if (loading) return <LoadingState message="Discovering recent research..." />;
  if (error) return <ErrorState title="Recent Research Unavailable" message={error} />;
  if (recent.length === 0) return <EmptyState title="No Recent Research" description="No significantly newer papers were identified in this domain." icon={CalendarDays} />;

  // Sort descending by year
  const sortedRecent = [...recent].sort((a, b) => (b.year || 0) - (a.year || 0));

  return (
    <div className="flex flex-col gap-8 animate-fade-in max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-2 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Recent Developments</h2>
          <p className="text-sm text-slate-500 mt-1">Research published after the target paper</p>
        </div>
        <span className="text-sm font-medium text-brand-600 bg-brand-50 px-4 py-2 rounded-xl border border-brand-100 flex items-center gap-2">
          <Zap className="w-4 h-4" /> {recent.length} Updates
        </span>
      </div>

      <div className="relative border-l-2 border-slate-200 ml-4 space-y-8 pb-8">
        {sortedRecent.map((rr) => (
          <RecentResearchCard key={rr.id} recent={rr} />
        ))}
      </div>
    </div>
  );
}

function RecentResearchCard({ recent }) {
  const rp = recent;
  
  return (
    <div className="relative pl-8">
      {/* Timeline dot */}
      <div className="absolute w-4 h-4 bg-brand-500 rounded-full -left-[9px] top-6 border-4 border-white shadow-sm"></div>
      
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:border-brand-300 transition-colors group">
        <div className="flex items-center gap-3 mb-3">
          <span className="text-lg font-black text-brand-600 tracking-tight">{rp.year || "New"}</span>
          <div className="h-px bg-slate-200 flex-1"></div>
          {recent.trend_type && (
            <Badge variant="primary" className="text-xs">{recent.trend_type}</Badge>
          )}
        </div>
        
        <h3 className="text-lg font-bold text-slate-900 mb-2 leading-snug group-hover:text-brand-700 transition-colors">
          {rp.title}
        </h3>
        
        <p className="text-sm text-slate-500 mb-4 line-clamp-2">
          {rp.authors || "Unknown Authors"}
        </p>
        
        {recent.novelty_description && (
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 mb-4">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Novel Contribution</h4>
            <p className="text-sm text-slate-600">{recent.novelty_description}</p>
          </div>
        )}
        
        <div className="flex items-center gap-4">
          {rp.doi && (
            <a 
              href={`https://doi.org/${rp.doi}`} 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-700 transition-colors"
            >
              Open Paper <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
          {rp.venue && (
            <span className="text-xs text-slate-500 max-w-[200px] truncate" title={rp.venue}>
              {rp.venue}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
