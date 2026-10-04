import { useEffect, useState, useMemo } from "react";
import { useOutletContext } from "react-router-dom";
import { literatureApi } from "../../../api";
import { LoadingState } from "../../common/LoadingState";
import { ErrorState } from "../../common/ErrorState";
import { EmptyState } from "../../common/EmptyState";
import CitationGraph from "../../CitationGraph";
import { Network, Search, SlidersHorizontal, Table as TableIcon, LayoutTemplate, ExternalLink } from "lucide-react";
import { Badge } from "../../common/Badge";

const RELATIONSHIP_COLORS = {
  'DIRECTLY_RELATED': '#0ea5e9', // sky-500
  'METHODOLOGICALLY_RELATED': '#8b5cf6', // violet-500
  'DOMAIN_RELATED': '#64748b', // slate-500
  'FOUNDATIONAL': '#f59e0b', // amber-500
  'RECENT_DEVELOPMENT': '#10b981', // emerald-500
  'ALTERNATIVE_APPROACH': '#ef4444', // red-500
  'OTHER_RELATED': '#94a3b8' // slate-400
};

export function ResearchGraph() {
  const { paper, pipelineStatus } = useOutletContext();
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("graph"); // "graph" or "table"
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("All");
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    if (!paper) return;
    
    const fetchLandscape = async () => {
      try {
        const data = await literatureApi.getRankedPapers(paper.id, 1, 100);
        setPapers(data.papers || data.items || []);
        setError(null);
      } catch (err) {
        if (err.status === 404) {
           setPapers([]);
        } else {
           setError(err.message || "Failed to load research landscape.");
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchLandscape();
  }, [paper]);

  const { graphData, availableTypes, yearRange, avgRelevance } = useMemo(() => {
    if (!paper || papers.length === 0) return { graphData: null, availableTypes: [], yearRange: [0,0], avgRelevance: 0 };
    
    const types = new Set();
    let minYear = 3000;
    let maxYear = 0;
    let totalRelevance = 0;
    let validScores = 0;

    const nodes = [
      {
        id: `paper_${paper.id}`,
        name: paper.title || "Target Paper",
        group: "target",
        year: paper.year,
        isTarget: true,
        val: 20
      }
    ];
    const links = [];

    const filteredPapers = papers.filter(rp => {
      const matchSearch = (rp.title || "").toLowerCase().includes(searchQuery.toLowerCase()) || 
                          (rp.authors || "").toLowerCase().includes(searchQuery.toLowerCase());
      const matchFilter = filterType === "All" || rp.relationship_type === filterType;
      return matchSearch && matchFilter;
    });

    filteredPapers.forEach(rp => {
      const related = rp;
      if (!related) return;

      const type = rp.relationship_type || 'OTHER_RELATED';
      types.add(type);
      
      if (related.year) {
        minYear = Math.min(minYear, related.year);
        maxYear = Math.max(maxYear, related.year);
      }
      if (rp.relevance_score !== null) {
        totalRelevance += rp.relevance_score;
        validScores++;
      }

      nodes.push({
        id: `related_${related.id}`,
        name: related.title || "Unknown Paper",
        group: type,
        year: related.year,
        authors: related.authors,
        relevance: rp.relevance_score,
        venue: related.venue,
        doi: related.doi,
        val: rp.relevance_score ? Math.max(5, Math.min(15, rp.relevance_score * 3)) : 5,
        originalData: rp
      });

      links.push({
        source: `paper_${paper.id}`,
        target: `related_${related.id}`,
        type: type
      });
    });

    return {
      graphData: { nodes, links },
      availableTypes: Array.from(types),
      yearRange: [minYear === 3000 ? paper.year || 2020 : minYear, Math.max(maxYear, paper.year || 0)],
      avgRelevance: validScores > 0 ? (totalRelevance / validScores) : 0
    };
  }, [paper, papers, filterType, searchQuery]);

  if (loading) return <LoadingState message="Preparing research landscape..." />;
  if (error) return <ErrorState title="Unable to load research landscape" message={error} />;
  
  const isProcessing = pipelineStatus?.status === "PROCESSING" && papers.length === 0;
  if (isProcessing) {
    return (
      <div className="p-16 text-center text-slate-500 border border-slate-200 rounded-xl bg-white flex flex-col items-center">
        <LoadingState message="Research landscape is being prepared... Related academic literature is still being analyzed." />
      </div>
    );
  }

  if (papers.length === 0) {
    return <EmptyState title="Research Landscape" description="No related research is available yet. The research landscape will appear here once related academic papers have been discovered." icon={Network} />;
  }

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  const getNodeColor = (node) => {
    if (node.isTarget) return '#0f172a'; // slate-900
    if (searchQuery && !node.name.toLowerCase().includes(searchQuery.toLowerCase()) && !(node.authors || "").toLowerCase().includes(searchQuery.toLowerCase())) {
      return '#e2e8f0'; // slate-200 (dimmed)
    }
    return RELATIONSHIP_COLORS[node.group] || RELATIONSHIP_COLORS['OTHER_RELATED'];
  };

  return (
    <div className="flex flex-col gap-6 animate-fade-in max-w-full">
      
      {/* Metrics Header */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-sm font-semibold text-slate-500 mb-1">Related Papers</p>
          <p className="text-2xl font-bold text-brand-600">{papers.length}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-sm font-semibold text-slate-500 mb-1">Relationship Types</p>
          <p className="text-2xl font-bold text-slate-800">{availableTypes.length}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-sm font-semibold text-slate-500 mb-1">Research Years</p>
          <p className="text-2xl font-bold text-slate-800">{yearRange[0]} - {yearRange[1]}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm text-center">
          <p className="text-sm font-semibold text-slate-500 mb-1">Average Relevance</p>
          <p className="text-2xl font-bold text-emerald-600">{avgRelevance.toFixed(2)}</p>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        
        {/* Left Sidebar - Controls */}
        <div className="lg:w-1/4 flex flex-col gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2 mb-4">
              <SlidersHorizontal className="w-4 h-4" /> Filters
            </h3>
            
            <div className="mb-4">
              <label className="text-xs font-semibold text-slate-500 mb-2 block">Search papers...</label>
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                <input 
                  type="text"
                  placeholder="Title or authors"
                  className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-brand-500"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            <div className="mb-4">
              <label className="text-xs font-semibold text-slate-500 mb-2 block">Relationship</label>
              <select 
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-brand-500"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="All">All Types</option>
                {availableTypes.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            
            <button 
              onClick={() => { setSearchQuery(""); setFilterType("All"); }}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 text-sm font-medium rounded-lg transition-colors"
            >
              Reset Filters
            </button>
          </div>

          {/* Details Panel */}
          {selectedNode && (
            <div className="bg-white p-5 rounded-2xl border border-brand-200 shadow-md">
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-sm font-bold text-brand-800 uppercase tracking-wider">Selected Node</h3>
                <button onClick={() => setSelectedNode(null)} className="text-slate-400 hover:text-slate-600 text-xl leading-none">&times;</button>
              </div>
              <p className="text-sm font-bold text-slate-900 leading-snug mb-2">{selectedNode.name}</p>
              
              {!selectedNode.isTarget && (
                <div className="space-y-3 mt-4">
                  <div className="flex justify-between text-sm border-b border-slate-100 pb-2">
                    <span className="text-slate-500">Year</span>
                    <span className="font-medium text-slate-800">{selectedNode.year || "Unknown"}</span>
                  </div>
                  <div className="flex justify-between text-sm border-b border-slate-100 pb-2">
                    <span className="text-slate-500">Relevance</span>
                    <span className="font-bold text-brand-600">{selectedNode.relevance?.toFixed(2) || "N/A"}</span>
                  </div>
                  <div className="pt-1">
                    <span className="text-xs text-slate-500 block mb-1">Relationship</span>
                    <Badge>{selectedNode.group}</Badge>
                  </div>
                  {selectedNode.doi && (
                    <div className="pt-2">
                      <a href={`https://doi.org/${selectedNode.doi}`} target="_blank" rel="noopener noreferrer" className="w-full inline-flex justify-center items-center gap-2 bg-slate-50 hover:bg-slate-100 text-slate-700 py-2 rounded-lg text-sm font-medium transition-colors border border-slate-200">
                        Open External Paper <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  )}
                  {!selectedNode.isTarget && selectedNode.id.startsWith("related_") && (
                    <div className="pt-1">
                      <button 
                        onClick={() => {
                          const paperId = selectedNode.id.replace("related_", "");
                          window.location.href = `/papers/${paper.id}/research/compare?papers=${paperId}`;
                        }}
                        className="w-full inline-flex justify-center items-center gap-2 bg-brand-50 hover:bg-brand-100 text-brand-700 py-2 rounded-lg text-sm font-medium transition-colors"
                      >
                        Compare With Target
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Main Content - Graph or Table */}
        <div className="lg:w-3/4 flex flex-col gap-4">
          <div className="flex justify-end gap-2 mb-[-10px] z-10 relative pr-4 pt-2">
            <button 
              onClick={() => setViewMode("graph")}
              className={`p-2 rounded-lg border flex items-center gap-2 text-sm font-medium transition-colors ${viewMode === 'graph' ? 'bg-white border-brand-200 text-brand-600 shadow-sm' : 'bg-transparent border-transparent text-slate-500 hover:bg-slate-200'}`}
            >
              <Network className="w-4 h-4" /> Graph
            </button>
            <button 
              onClick={() => setViewMode("table")}
              className={`p-2 rounded-lg border flex items-center gap-2 text-sm font-medium transition-colors ${viewMode === 'table' ? 'bg-white border-brand-200 text-brand-600 shadow-sm' : 'bg-transparent border-transparent text-slate-500 hover:bg-slate-200'}`}
            >
              <TableIcon className="w-4 h-4" /> Table
            </button>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            {viewMode === "graph" ? (
              <CitationGraph 
                graphData={graphData} 
                onNodeClick={handleNodeClick} 
                nodeColor={getNodeColor}
              />
            ) : (
              <div className="overflow-x-auto p-1">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
                      <th className="p-4 font-semibold border-b border-slate-200">Paper</th>
                      <th className="p-4 font-semibold border-b border-slate-200">Year</th>
                      <th className="p-4 font-semibold border-b border-slate-200">Relationship</th>
                      <th className="p-4 font-semibold border-b border-slate-200">Relevance</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {graphData.nodes.filter(n => !n.isTarget).map(node => (
                      <tr key={node.id} className="hover:bg-slate-50 cursor-pointer" onClick={() => setSelectedNode(node)}>
                        <td className="p-4 text-sm text-slate-800 font-medium max-w-xs truncate" title={node.name}>{node.name}</td>
                        <td className="p-4 text-sm text-slate-600">{node.year || "-"}</td>
                        <td className="p-4 text-sm"><Badge variant="default" className="text-xs">{node.group}</Badge></td>
                        <td className="p-4 text-sm font-bold text-brand-600">{node.relevance?.toFixed(2) || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
