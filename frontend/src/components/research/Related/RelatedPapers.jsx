import { useEffect, useState } from "react";
import { useOutletContext, useNavigate } from "react-router-dom";
import { literatureApi } from "../../../api";
import { LoadingState } from "../../common/LoadingState";
import { ErrorState } from "../../common/ErrorState";
import { Badge } from "../../common/Badge";
import { EmptyState } from "../../common/EmptyState";
import { Network, ExternalLink, TrendingUp, CheckSquare, Square } from "lucide-react";

export function RelatedPapers() {
  const { paper } = useOutletContext();
  const navigate = useNavigate();
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedForCompare, setSelectedForCompare] = useState(new Set());

  useEffect(() => {
    if (!paper) return;
    
    const fetchRelated = async () => {
      try {
        const data = await literatureApi.getRankedPapers(paper.id, 1, 50);
        setPapers(data.papers || data.items || []);
        setError(null);
      } catch (err) {
        if (err.status === 404) {
           setPapers([]);
        } else {
           setError(err.message || "Failed to load related papers.");
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchRelated();
  }, [paper]);

  const toggleSelect = (id) => {
    const newSet = new Set(selectedForCompare);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      if (newSet.size >= 3) {
        alert("Maximum 3 comparison papers can be selected.");
        return;
      }
      newSet.add(id);
    }
    setSelectedForCompare(newSet);
  };

  const handleCompare = () => {
    if (selectedForCompare.size === 0) return;
    const paperIds = Array.from(selectedForCompare).join(',');
    navigate(`/papers/${paper.id}/research/compare?papers=${paperIds}`);
  };

  if (loading) return <LoadingState message="Loading related research..." />;
  if (error) return <ErrorState title="Unable to Load Papers" message={error} />;
  if (papers.length === 0) return <EmptyState title="No Related Papers" description="No related literature has been discovered for this paper yet." icon={Network} />;

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold text-slate-900">Discovered Literature</h2>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-full">{papers.length} Papers</span>
          <button
            onClick={handleCompare}
            disabled={selectedForCompare.size === 0}
            className={`px-4 py-2 rounded-xl font-medium text-sm transition-colors ${
              selectedForCompare.size > 0 
                ? 'bg-brand-600 hover:bg-brand-700 text-white shadow-sm' 
                : 'bg-slate-100 text-slate-400 cursor-not-allowed'
            }`}
          >
            Compare Selected {selectedForCompare.size > 0 && `(${selectedForCompare.size})`}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {papers.map((rp) => (
          <RelatedPaperCard 
            key={rp.id} 
            related={rp} 
            isSelected={selectedForCompare.has(rp.id)}
            onToggle={() => toggleSelect(rp.id)}
          />
        ))}
      </div>
    </div>
  );
}

function RelatedPaperCard({ related, isSelected, onToggle }) {
  const rp = related;
  
  const getRelationshipBadge = (type) => {
    switch (type) {
      case 'DIRECTLY_RELATED': return <Badge variant="primary">Directly Related</Badge>;
      case 'METHODOLOGICALLY_RELATED': return <Badge variant="info">Methodologically Related</Badge>;
      case 'DOMAIN_RELATED': return <Badge variant="default">Domain Related</Badge>;
      case 'FOUNDATIONAL': return <Badge variant="warning">Foundational</Badge>;
      case 'RECENT_DEVELOPMENT': return <Badge variant="success">Recent Development</Badge>;
      case 'ALTERNATIVE_APPROACH': return <Badge variant="error">Alternative Approach</Badge>;
      default: return <Badge>{type}</Badge>;
    }
  };

  return (
    <div className={`bg-white p-6 rounded-2xl shadow-sm border transition-colors ${isSelected ? 'border-brand-500 ring-1 ring-brand-500 ring-opacity-50' : 'border-slate-200 hover:border-brand-300'}`}>
      <div className="flex flex-col md:flex-row gap-6">
        
        <div className="pt-1 hidden md:block">
          <button 
            onClick={onToggle}
            className="text-slate-400 hover:text-brand-500 focus:outline-none transition-colors"
            title="Select for comparison"
          >
            {isSelected ? <CheckSquare className="w-6 h-6 text-brand-500" /> : <Square className="w-6 h-6" />}
          </button>
        </div>

        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <button 
              onClick={onToggle}
              className="md:hidden text-slate-400 focus:outline-none transition-colors"
            >
              {isSelected ? <CheckSquare className="w-5 h-5 text-brand-500" /> : <Square className="w-5 h-5" />}
            </button>
            {getRelationshipBadge(related.relationship_type)}
            <span className="text-xs font-medium text-slate-400">•</span>
            <span className="text-sm font-medium text-slate-600">{rp.year || "Unknown Year"}</span>
            {rp.citation_count !== null && (
              <>
                <span className="text-xs font-medium text-slate-400">•</span>
                <span className="text-sm font-medium text-slate-600 flex items-center gap-1">
                  <TrendingUp className="w-3.5 h-3.5" /> {rp.citation_count} citations
                </span>
              </>
            )}
          </div>
          
          <h3 className="text-lg font-bold text-slate-900 mb-2 leading-snug">
            {rp.title}
          </h3>
          
          <p className="text-sm text-slate-500 mb-4 line-clamp-2">
            {rp.authors || "Unknown Authors"}
          </p>
          
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
              <span className="text-sm text-slate-500 max-w-[200px] truncate" title={rp.venue}>
                {rp.venue}
              </span>
            )}
          </div>
        </div>
        
        {related.relevance_score !== null && (
          <div className="flex-shrink-0 md:w-48 bg-slate-50 rounded-xl p-4 border border-slate-100 flex flex-col justify-center">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Research Relevance</span>
            </div>
            <div className="text-3xl font-bold text-brand-600 mb-1">
              {related.relevance_score.toFixed(2)}
            </div>
            <p className="text-[10px] text-slate-400 leading-tight">
              Relevance indicates how closely this paper matches the target paper based on the literature matching system. It is not an academic quality rating.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
