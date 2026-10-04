import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { literatureApi } from "../../../api";
import { LoadingState } from "../../common/LoadingState";
import { ErrorState } from "../../common/ErrorState";
import { EmptyState } from "../../common/EmptyState";
import { Search, Lightbulb, TrendingUp } from "lucide-react";
import { Badge } from "../../common/Badge";

export function ResearchGaps() {
  const { paper } = useOutletContext();
  const [gaps, setGaps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!paper) return;
    
    const fetchGaps = async () => {
      try {
        const data = await literatureApi.getResearchGaps(paper.id);
        setGaps(data.gaps || data || []);
        setError(null);
      } catch (err) {
        if (err.status === 404) {
           setGaps([]);
        } else {
           setError(err.message || "Failed to load research gaps.");
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchGaps();
  }, [paper]);

  if (loading) return <LoadingState message="Detecting research gaps..." />;
  if (error) return <ErrorState title="Gaps Unavailable" message={error} />;
  if (gaps.length === 0) return <EmptyState title="No Gaps Detected" description="No significant research gaps have been identified in the surveyed literature." icon={Search} />;

  return (
    <div className="flex flex-col gap-8 animate-fade-in">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold text-slate-900">Identified Research Gaps</h2>
        <span className="text-sm font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-full">{gaps.length} Gaps Detected</span>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {gaps.map((gap) => (
          <GapCard key={gap.id} gap={gap} />
        ))}
      </div>
    </div>
  );
}

function GapCard({ gap }) {
  const getGapBadge = (type) => {
    switch (type) {
      case 'METHODOLOGICAL_GAP': return <Badge variant="info">Methodological Gap</Badge>;
      case 'EMPIRICAL_GAP': return <Badge variant="warning">Empirical Gap</Badge>;
      case 'THEORETICAL_GAP': return <Badge variant="default">Theoretical Gap</Badge>;
      case 'CONCEPTUAL_GAP': return <Badge variant="primary">Conceptual Gap</Badge>;
      case 'DATASET_GAP': return <Badge variant="error">Dataset Gap</Badge>;
      case 'APPLICATION_GAP': return <Badge variant="success">Application Gap</Badge>;
      default: return <Badge>{type}</Badge>;
    }
  };

  return (
    <div className="bg-white p-6 md:p-8 rounded-2xl shadow-sm border border-slate-200">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div>
          <div className="mb-3">{getGapBadge(gap.gap_type)}</div>
          <h3 className="text-xl font-bold text-slate-900 leading-snug">{gap.title}</h3>
        </div>
        <div className="bg-amber-50 px-4 py-2 rounded-xl border border-amber-100 flex-shrink-0 text-center min-w-[120px]">
          <span className="block text-xs font-bold text-amber-600 uppercase tracking-wider mb-1">Confidence</span>
          <span className="text-xl font-black text-amber-700">{(gap.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>

      <div className="mb-6">
        <p className="text-slate-700 text-lg leading-relaxed">{gap.description}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-50 p-5 rounded-xl border border-slate-100">
          <h4 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Search className="w-4 h-4 text-brand-500" /> Supporting Evidence
          </h4>
          <ul className="space-y-2">
            {gap.evidence?.map((ev, i) => (
              <li key={i} className="text-sm text-slate-600 flex gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 flex-shrink-0"></span>
                <span>{ev}</span>
              </li>
            ))}
          </ul>
        </div>
        
        <div className="bg-emerald-50 p-5 rounded-xl border border-emerald-100">
          <h4 className="text-sm font-bold text-emerald-800 uppercase tracking-wider mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-600" /> Proposed Direction
          </h4>
          <p className="text-sm text-emerald-700 leading-relaxed">
            {gap.proposed_direction}
          </p>
        </div>
      </div>
    </div>
  );
}
