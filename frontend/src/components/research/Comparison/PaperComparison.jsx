import { useEffect, useState, useMemo } from "react";
import { useOutletContext, useSearchParams, useNavigate } from "react-router-dom";
import { literatureApi } from "../../../api";
import { LoadingState } from "../../common/LoadingState";
import { ErrorState } from "../../common/ErrorState";
import { Badge } from "../../common/Badge";
import { Search, Plus, X, GitCompare, ExternalLink, Network, FileSearch } from "lucide-react";

export function PaperComparison() {
  const { paper } = useOutletContext();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rankedPapers, setRankedPapers] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [targetProfile, setTargetProfile] = useState(null);

  const selectedPaperIds = useMemo(() => {
    const ids = searchParams.get('papers');
    return ids ? ids.split(',').map(id => parseInt(id, 10)).filter(id => !isNaN(id)) : [];
  }, [searchParams]);

  useEffect(() => {
    if (!paper) return;
    
    const fetchComparisonData = async () => {
      setLoading(true);
      try {
        const [rankedRes, profileRes, analysisRes] = await Promise.allSettled([
          literatureApi.getRankedPapers(paper.id, 1, 100),
          literatureApi.getResearchProfile(paper.id),
          literatureApi.getLiteratureAnalysis(paper.id)
        ]);
        
        if (rankedRes.status === "fulfilled") {
          setRankedPapers(rankedRes.value.papers || rankedRes.value.items || []);
        } else if (rankedRes.reason?.status !== 404) {
          throw rankedRes.reason;
        }

        if (profileRes.status === "fulfilled") {
          setTargetProfile(profileRes.value);
        }

        if (analysisRes.status === "fulfilled") {
          setAnalyses(analysisRes.value || []);
        } else if (analysisRes.reason?.status !== 404) {
          console.warn("Analysis not found");
        }

        setError(null);
      } catch (err) {
        setError(err.message || "Failed to load comparison data.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchComparisonData();
  }, [paper]);

  const handleSelectPaper = (id) => {
    if (selectedPaperIds.includes(id)) return;
    if (selectedPaperIds.length >= 3) {
      alert("Maximum 3 comparison papers can be selected.");
      return;
    }
    const newIds = [...selectedPaperIds, id];
    setSearchParams({ papers: newIds.join(',') });
  };

  const handleRemovePaper = (id) => {
    const newIds = selectedPaperIds.filter(pid => pid !== id);
    if (newIds.length > 0) {
      setSearchParams({ papers: newIds.join(',') });
    } else {
      setSearchParams({});
    }
  };

  if (loading) return <LoadingState message="Loading comparison data..." />;
  if (error) return <ErrorState title="Comparison Unavailable" message={error} />;

  const selectedPapersDetails = rankedPapers.filter(rp => selectedPaperIds.includes(rp.id));

  return (
    <div className="flex flex-col gap-8 animate-fade-in max-w-full overflow-x-hidden">
      
      {/* Selection Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <GitCompare className="w-5 h-5 text-brand-600" /> Compare Research Papers
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="relative group border-2 border-brand-500 rounded-xl p-4 bg-brand-50/50">
            <div className="absolute top-0 right-0 transform translate-x-1/3 -translate-y-1/3 bg-brand-500 text-white text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full shadow-sm">Target</div>
            <h3 className="text-sm font-bold text-slate-900 line-clamp-2" title={paper.title}>{paper.title}</h3>
            <p className="text-xs text-slate-500 mt-1">{paper.year || "Unknown Year"}</p>
          </div>
          
          {selectedPaperIds.map((id, index) => {
            const rp = selectedPapersDetails.find(p => p.id === id);
            if (!rp) return null;
            return (
              <div key={id} className="relative border border-slate-200 rounded-xl p-4 bg-slate-50 flex flex-col justify-between">
                <button onClick={() => handleRemovePaper(id)} className="absolute top-2 right-2 text-slate-400 hover:text-red-500 bg-white rounded-full p-0.5 shadow-sm border border-slate-200 transition-colors">
                  <X className="w-3.5 h-3.5" />
                </button>
                <h3 className="text-sm font-bold text-slate-800 line-clamp-2 mb-2 pr-4" title={rp.title}>{rp.title}</h3>
                <div>
                  <Badge variant="default" className="text-[10px]">{rp.relationship_type}</Badge>
                  <p className="text-[10px] text-slate-500 mt-1">Relevance: <span className="font-bold text-brand-600">{rp.relevance_score?.toFixed(2)}</span></p>
                </div>
              </div>
            );
          })}
          
          {selectedPaperIds.length < 3 && (
             <PaperSelector 
               rankedPapers={rankedPapers} 
               selectedIds={selectedPaperIds} 
               onSelect={handleSelectPaper} 
             />
          )}
        </div>
      </div>

      {selectedPaperIds.length === 0 ? (
        <div className="bg-slate-50 p-12 rounded-2xl border border-slate-200 text-center flex flex-col items-center justify-center">
          <div className="bg-white p-4 rounded-full shadow-sm mb-4 text-brand-500">
            <GitCompare className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-2">Select papers to compare</h3>
          <p className="text-sm text-slate-500 max-w-md">Select up to 3 related papers from the list above to compare their methodologies, findings, and research directions against the target paper.</p>
        </div>
      ) : (
        <ComparisonView 
          paper={paper} 
          targetProfile={targetProfile}
          selectedPapers={selectedPapersDetails} 
          analyses={analyses} 
        />
      )}

    </div>
  );
}

function PaperSelector({ rankedPapers, selectedIds, onSelect }) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  
  const availablePapers = rankedPapers.filter(rp => !selectedIds.includes(rp.id));
  const filteredPapers = availablePapers.filter(rp => 
    (rp.title || "").toLowerCase().includes(search.toLowerCase()) ||
    (rp.authors || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="relative">
      {!isOpen ? (
        <button 
          onClick={() => setIsOpen(true)}
          className="w-full h-full min-h-[100px] border-2 border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center text-slate-500 hover:text-brand-600 hover:border-brand-300 hover:bg-brand-50 transition-colors"
        >
          <Plus className="w-6 h-6 mb-1" />
          <span className="text-xs font-semibold">Add Paper</span>
        </button>
      ) : (
        <div className="absolute top-0 left-0 w-full md:w-[350px] z-20 bg-white rounded-xl shadow-xl border border-slate-200 flex flex-col overflow-hidden max-h-[400px]">
          <div className="p-3 border-b border-slate-100 flex items-center justify-between bg-slate-50">
            <div className="relative flex-1 mr-2">
              <Search className="w-4 h-4 absolute left-2.5 top-2 text-slate-400" />
              <input 
                type="text" 
                autoFocus
                placeholder="Search to compare..." 
                className="w-full pl-8 pr-2 py-1.5 text-sm rounded-lg border border-slate-200 focus:outline-none focus:border-brand-500"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>
            <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-slate-700">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="overflow-y-auto p-2 space-y-1">
            {filteredPapers.length === 0 ? (
              <p className="text-xs text-center text-slate-500 py-4">No available papers match.</p>
            ) : (
              filteredPapers.map(rp => (
                <button 
                  key={rp.id}
                  onClick={() => { onSelect(rp.id); setIsOpen(false); setSearch(""); }}
                  className="w-full text-left p-3 hover:bg-slate-50 rounded-lg transition-colors border border-transparent hover:border-slate-100 flex flex-col gap-1"
                >
                  <span className="text-xs font-bold text-slate-900 line-clamp-2">{rp.title}</span>
                  <div className="flex justify-between items-center w-full">
                    <span className="text-[10px] text-slate-500 truncate mr-2">{rp.authors}</span>
                    <span className="text-[10px] font-bold text-brand-600 shrink-0 border border-brand-100 bg-brand-50 px-1.5 rounded">{rp.relevance_score?.toFixed(2)}</span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ComparisonView({ paper, targetProfile, selectedPapers, analyses }) {
  // Map selected papers to columns
  const columns = [
    {
      id: `target_${paper.id}`,
      type: "target",
      title: paper.title,
      authors: paper.authors?.join(", "),
      year: paper.year,
      url: null, // target might not have url easily accessible without doi
      analysis: {
        problem: paper.problem_statement,
        objective: paper.objective,
        methodology: paper.methodology || targetProfile?.methodology,
        methods: targetProfile?.methods,
        algorithms: targetProfile?.algorithms,
        models: targetProfile?.models,
        datasets: paper.dataset ? [paper.dataset] : targetProfile?.datasets,
        findings: paper.results,
        contributions: paper.contributions,
        limitations: paper.limitations,
        future: paper.future_work,
      }
    },
    ...selectedPapers.map(rp => {
      const a = analyses.find(an => an.related_paper_id === rp.id);
      return {
        id: `related_${rp.id}`,
        type: "related",
        title: rp.title,
        authors: rp.authors,
        year: rp.year,
        url: rp.doi ? `https://doi.org/${rp.doi}` : null,
        relevance: rp.relevance_score,
        relationship: rp.relationship_type,
        hasAnalysis: !!a,
        analysis: a ? {
          problem: a.problem_statement,
          objective: a.objective,
          methodology: a.methodology,
          methods: a.methods,
          algorithms: a.algorithms,
          models: a.models,
          datasets: a.datasets || (a.experimental_setup ? [a.experimental_setup] : []),
          findings: a.key_findings,
          contributions: a.contributions,
          limitations: a.limitations,
          future: a.research_direction,
          similarities: a.similarities,
          differences: a.differences
        } : null
      };
    })
  ];

  const renderCellContent = (content) => {
    if (content === null || content === undefined || content === "" || (Array.isArray(content) && content.length === 0)) {
      return <span className="text-slate-400 italic text-sm">Not available</span>;
    }
    
    if (Array.isArray(content)) {
      return (
        <ul className="space-y-1.5">
          {content.map((item, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-700">
              <span className="w-1 h-1 rounded-full bg-brand-400 mt-2 flex-shrink-0"></span>
              <span className="leading-snug">{item}</span>
            </li>
          ))}
        </ul>
      );
    }
    
    return <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{content}</div>;
  };

  const renderBadges = (content) => {
    if (!content || (Array.isArray(content) && content.length === 0)) {
      return <span className="text-slate-400 italic text-sm">Not available</span>;
    }
    const arr = Array.isArray(content) ? content : [content];
    return (
      <div className="flex flex-wrap gap-1.5">
        {arr.map((item, i) => (
          <Badge key={i} variant="default" className="text-xs bg-slate-100 text-slate-700 border-slate-200">{item}</Badge>
        ))}
      </div>
    );
  };

  const ComparisonRow = ({ title, dataKey, type = "text" }) => {
    return (
      <tr className="border-t border-slate-200">
        <td className="bg-slate-50 p-3 font-bold text-xs text-slate-500 uppercase tracking-wider align-top border-r border-slate-200">
          {title}
        </td>
        {columns.map((col, index) => {
          const isEmpty = col.type === "related" && !col.hasAnalysis;
          const content = !isEmpty ? col.analysis[dataKey] : null;
          return (
            <td key={col.id} className="p-5 w-[320px] align-top border-r border-slate-100 last:border-r-0">
              {isEmpty ? (
                <div className="flex items-center gap-2 text-slate-400 text-sm italic">
                  <FileSearch className="w-4 h-4" /> Analysis unavailable
                </div>
              ) : (
                type === "badge" ? renderBadges(content) : renderCellContent(content)
              )}
            </td>
          );
        })}
      </tr>
    );
  };

  return (
    <div className="flex flex-col gap-8">
      
      {/* Similarities & Differences */}
      {selectedPapers.some(rp => columns.find(c => c.id === `related_${rp.id}`)?.analysis?.similarities?.length > 0) && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="bg-slate-50 p-4 border-b border-slate-200">
            <h3 className="font-bold text-slate-900 flex items-center gap-2">Target Paper vs Related Papers</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-100">
            <div className="p-6 bg-emerald-50/30">
              <h4 className="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-4">Shared Aspects (Similarities)</h4>
              <div className="space-y-4">
                {columns.filter(c => c.type === "related" && c.hasAnalysis && c.analysis.similarities?.length > 0).map(col => (
                  <div key={col.id}>
                    <p className="text-xs font-semibold text-slate-500 mb-2">{col.title}</p>
                    <ul className="space-y-1 text-sm text-emerald-800">
                      {col.analysis.similarities.map((sim, i) => (
                        <li key={i} className="flex gap-2"><span className="text-emerald-500">✓</span> {sim}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
            <div className="p-6 bg-amber-50/30">
              <h4 className="text-xs font-bold text-amber-700 uppercase tracking-wider mb-4">Diverging Aspects (Differences)</h4>
              <div className="space-y-4">
                {columns.filter(c => c.type === "related" && c.hasAnalysis && c.analysis.differences?.length > 0).map(col => (
                  <div key={col.id}>
                    <p className="text-xs font-semibold text-slate-500 mb-2">{col.title}</p>
                    <ul className="space-y-1 text-sm text-amber-800">
                      {col.analysis.differences.map((diff, i) => (
                        <li key={i} className="flex gap-2"><span className="text-amber-500">△</span> {diff}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Structural Comparison */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-x-auto custom-scrollbar">
        <table className="w-full text-left border-collapse min-w-max">
          
          {/* Table Header */}
          <thead className="bg-white">
            <tr>
              <th className="p-0 border-r border-slate-200 border-b min-w-[200px] align-bottom">
                <span className="sr-only">Research Aspect</span>
              </th>
              {columns.map(col => (
                <th key={col.id} className="p-5 w-[320px] font-normal border-r border-slate-200 border-b last:border-r-0 align-top">
                  <div className="flex flex-col h-full justify-between">
                    <div>
                      {col.type === "target" ? (
                        <Badge variant="primary" className="mb-2 w-max">Target Paper</Badge>
                      ) : (
                        <div className="flex flex-wrap gap-1 mb-2">
                          <Badge variant="default">{col.relationship}</Badge>
                          <Badge variant="default" className="bg-brand-50 text-brand-700 border-brand-100">{col.relevance?.toFixed(2)}</Badge>
                        </div>
                      )}
                      <h3 className="font-bold text-slate-900 leading-snug mb-1 line-clamp-3" title={col.title}>{col.title}</h3>
                      <p className="text-xs text-slate-500 mb-3">{col.year || "Unknown"} • {col.authors}</p>
                    </div>
                    {col.url && (
                      <a href={col.url} target="_blank" rel="noopener noreferrer" className="mt-auto inline-flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700">
                        Open Paper <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          {/* Rows */}
          <tbody>
            <ComparisonRow title="Research Problem" dataKey="problem" />
            <ComparisonRow title="Objective" dataKey="objective" />
            <ComparisonRow title="Methodology" dataKey="methodology" />
            <ComparisonRow title="Methods" dataKey="methods" type="badge" />
            <ComparisonRow title="Algorithms" dataKey="algorithms" type="badge" />
            <ComparisonRow title="Models" dataKey="models" type="badge" />
            <ComparisonRow title="Datasets / Setup" dataKey="datasets" type="badge" />
            <ComparisonRow title="Key Findings / Results" dataKey="findings" />
            <ComparisonRow title="Contributions" dataKey="contributions" />
            <ComparisonRow title="Limitations" dataKey="limitations" />
            <ComparisonRow title="Research Direction" dataKey="future" />
          </tbody>
        </table>
      </div>
    </div>
  );
}
