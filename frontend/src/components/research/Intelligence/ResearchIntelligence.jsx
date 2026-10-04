import { useEffect, useState, useMemo } from "react";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { literatureApi } from "../../../api";
import { LoadingState } from "../../common/LoadingState";
import { ErrorState } from "../../common/ErrorState";
import { Badge } from "../../common/Badge";
import { EmptyState } from "../../common/EmptyState";
import { Search, ChevronRight, LayoutTemplate, Target, CheckCircle2, AlertCircle, X, ExternalLink, Lightbulb } from "lucide-react";

export function ResearchIntelligence() {
  const { paper, pipelineStatus } = useOutletContext();
  const [searchParams, setSearchParams] = useSearchParams();
  const currentTab = searchParams.get("tab") || "opportunities";
  
  const [gaps, setGaps] = useState([]);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!paper) return;
    
    const fetchData = async () => {
      setLoading(true);
      try {
        const [gapsRes, recentRes] = await Promise.allSettled([
          literatureApi.getResearchGaps(paper.id),
          literatureApi.getRecentResearch(paper.id, 1, 50)
        ]);
        
        if (gapsRes.status === "fulfilled") {
          setGaps(gapsRes.value.gaps || []);
        } else if (gapsRes.reason?.status !== 404) {
          throw gapsRes.reason;
        }

        if (recentRes.status === "fulfilled") {
          setRecent(recentRes.value.recent_research || recentRes.value.papers || recentRes.value.items || []);
        } else if (recentRes.reason?.status !== 404) {
          throw recentRes.reason;
        }
        
        setError(null);
      } catch (err) {
        setError(err.message || "Failed to load research intelligence data.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [paper]);

  const setTab = (tab) => {
    setSearchParams({ tab });
  };

  const isProcessing = pipelineStatus?.status === "PROCESSING" && gaps.length === 0 && recent.length === 0;

  if (loading) return <LoadingState message="Compiling research intelligence..." />;
  if (error) return <ErrorState title="Intelligence Unavailable" message={error} />;
  
  if (isProcessing) {
    return (
      <div className="p-16 text-center text-slate-500 border border-slate-200 rounded-xl bg-white flex flex-col items-center">
        <LoadingState message="Research intelligence is being prepared. Some sections may become available as analysis completes." />
      </div>
    );
  }

  const gapCategories = new Set(gaps.map(g => g.gap_type));
  const recentAddressesGapCount = recent.filter(r => r.addresses_gap).length;
  const recentWindow = recent.length > 0 ? `${Math.min(...recent.map(r => r.year))}–${Math.max(...recent.map(r => r.year))}` : "N/A";

  return (
    <div className="flex flex-col gap-6 animate-fade-in max-w-full">
      {/* Header Summary */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900 mb-2 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-500" /> Research Intelligence
          </h2>
          <p className="text-sm text-slate-500 max-w-xl">
            {gaps.length} research {gaps.length === 1 ? 'gap' : 'gaps'} identified. {recent.length} recent papers were found within the configured recent-research window. {recentAddressesGapCount} recent {recentAddressesGapCount === 1 ? 'paper is' : 'papers are'} explicitly associated with identified research gaps.
          </p>
        </div>
        
        <div className="flex gap-4">
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Gaps</span>
            <span className="text-xl font-black text-slate-800">{gaps.length}</span>
          </div>
          <div className="w-px h-8 bg-slate-200 self-center"></div>
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Categories</span>
            <span className="text-xl font-black text-slate-800">{gapCategories.size}</span>
          </div>
          <div className="w-px h-8 bg-slate-200 self-center"></div>
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Recent Papers</span>
            <span className="text-xl font-black text-slate-800">{recent.length}</span>
          </div>
          <div className="w-px h-8 bg-slate-200 self-center"></div>
          <div className="flex flex-col">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Window</span>
            <span className="text-xl font-black text-slate-800">{recentWindow}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200">
        <button 
          onClick={() => setTab("opportunities")} 
          className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${currentTab === 'opportunities' ? 'border-brand-500 text-brand-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          Research Opportunities
        </button>
        <button 
          onClick={() => setTab("gaps")} 
          className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${currentTab === 'gaps' ? 'border-brand-500 text-brand-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          Research Gaps
        </button>
        <button 
          onClick={() => setTab("recent")} 
          className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${currentTab === 'recent' ? 'border-brand-500 text-brand-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
        >
          Recent Developments
        </button>
      </div>

      {/* Content */}
      <div className="mt-2">
        {currentTab === "opportunities" && <OpportunitiesView gaps={gaps} recent={recent} paper={paper} />}
        {currentTab === "gaps" && <GapsView gaps={gaps} paper={paper} />}
        {currentTab === "recent" && <RecentView recent={recent} paper={paper} />}
      </div>
    </div>
  );
}

function OpportunitiesView({ gaps, recent, paper }) {
  if (gaps.length === 0) {
    return <EmptyState title="No Opportunities Detected" description="No research gaps with connected recent work were identified." />;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-6">
        {gaps.map((gap, index) => {
          const linkedRecent = recent.filter(r => r.addresses_gap && r.related_gap_ids?.includes(index + 1) || (r.addresses_gap && !r.related_gap_ids)); // Approximate linkage if IDs aren't perfectly mapped
          return (
            <div key={index} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-8">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-3">
                  <Badge variant="warning">{gap.gap_type}</Badge>
                  <span className="text-sm font-semibold text-slate-400">Confidence: {(gap.confidence * 100).toFixed(0)}%</span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{gap.title}</h3>
                <p className="text-sm text-slate-600 mb-4">{gap.description}</p>
                
                {gap.proposed_direction && (
                  <div className="bg-amber-50 p-4 rounded-xl border border-amber-100">
                    <h4 className="text-xs font-bold text-amber-700 uppercase tracking-wider mb-2">Proposed Direction</h4>
                    <p className="text-sm text-amber-900 leading-relaxed">{gap.proposed_direction}</p>
                  </div>
                )}
              </div>

              <div className="md:w-1/3 flex flex-col">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Recent Related Work ({linkedRecent.length})</h4>
                {linkedRecent.length === 0 ? (
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-sm text-slate-500 text-center italic">
                    No recent papers are explicitly associated with this gap.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {linkedRecent.slice(0, 3).map(r => (
                      <div key={r.id} className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                        <p className="text-xs font-bold text-slate-900 line-clamp-2 mb-1" title={r.title}>{r.title}</p>
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] text-slate-500">{r.year}</span>
                          <span className="text-[10px] font-bold text-brand-600">Rel: {r.relevance_score?.toFixed(2)}</span>
                        </div>
                      </div>
                    ))}
                    {linkedRecent.length > 3 && (
                      <div className="text-xs font-medium text-slate-500 text-center pt-2">
                        + {linkedRecent.length - 3} more
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function GapsView({ gaps, paper }) {
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("All");
  const [selectedGap, setSelectedGap] = useState(null);

  const gapTypes = ["All", ...new Set(gaps.map(g => g.gap_type))];

  const filteredGaps = gaps.filter(g => {
    const matchSearch = (g.title || "").toLowerCase().includes(search.toLowerCase()) || 
                        (g.description || "").toLowerCase().includes(search.toLowerCase()) ||
                        (g.proposed_direction || "").toLowerCase().includes(search.toLowerCase());
    const matchType = filterType === "All" || g.gap_type === filterType;
    return matchSearch && matchType;
  });

  if (gaps.length === 0) {
    return <EmptyState title="No Research Gaps" description="No research gaps were identified for this paper." />;
  }

  return (
    <div className="flex flex-col gap-6 relative">
      <div className="flex flex-col md:flex-row gap-4 mb-2">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search research gaps..." 
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-brand-500"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <select 
          className="p-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:border-brand-500"
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
        >
          {gapTypes.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {filteredGaps.map((gap, i) => (
          <div key={i} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-brand-300 transition-colors cursor-pointer" onClick={() => setSelectedGap(gap)}>
            <div>
              <div className="flex items-center justify-between mb-3">
                <Badge variant="default">{gap.gap_type}</Badge>
                <div className="flex flex-col items-end w-24">
                  <div className="w-full bg-slate-100 rounded-full h-1.5 mb-1">
                    <div className="bg-brand-500 h-1.5 rounded-full" style={{ width: `${Math.min(100, Math.max(0, gap.confidence * 100))}%` }}></div>
                  </div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Conf: {(gap.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
              <h3 className="font-bold text-slate-900 mb-2 leading-snug">{gap.title}</h3>
              <p className="text-sm text-slate-600 line-clamp-3 mb-4">{gap.description}</p>
            </div>
            {gap.proposed_direction && (
              <div className="text-xs font-semibold text-brand-700 bg-brand-50 px-3 py-2 rounded-lg truncate">
                Dir: {gap.proposed_direction}
              </div>
            )}
          </div>
        ))}
      </div>

      {selectedGap && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/20 backdrop-blur-sm animate-fade-in" onClick={() => setSelectedGap(null)}>
          <div className="w-full max-w-md bg-white h-full shadow-2xl animate-slide-in-right overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-100 flex items-start justify-between sticky top-0 bg-white/95 backdrop-blur z-10">
              <div>
                <Badge variant="default" className="mb-2">{selectedGap.gap_type}</Badge>
                <h3 className="text-lg font-bold text-slate-900 leading-snug pr-4">{selectedGap.title}</h3>
              </div>
              <button onClick={() => setSelectedGap(null)} className="p-2 text-slate-400 hover:text-slate-800 bg-slate-50 hover:bg-slate-100 rounded-full transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-8">
              <section>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Description</h4>
                <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{selectedGap.description}</p>
              </section>

              <section>
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Confidence</h4>
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-slate-100 rounded-full h-2">
                    <div className="bg-brand-500 h-2 rounded-full" style={{ width: `${Math.min(100, Math.max(0, selectedGap.confidence * 100))}%` }}></div>
                  </div>
                  <span className="text-sm font-bold text-slate-700">{(selectedGap.confidence * 100).toFixed(0)}%</span>
                </div>
              </section>

              {selectedGap.proposed_direction && (
                <section>
                  <h4 className="text-xs font-bold text-amber-700 uppercase tracking-wider mb-2">Proposed Direction</h4>
                  <div className="bg-amber-50 p-4 rounded-xl border border-amber-100">
                    <p className="text-sm text-amber-900 leading-relaxed">{selectedGap.proposed_direction}</p>
                  </div>
                </section>
              )}

              {selectedGap.evidence && (
                <section>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Evidence</h4>
                  {Array.isArray(selectedGap.evidence) ? (
                    <ul className="space-y-2">
                      {selectedGap.evidence.map((ev, i) => (
                        <li key={i} className="text-sm text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100 flex gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" /> 
                          <span className="leading-snug">{ev}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-slate-700">{selectedGap.evidence}</p>
                  )}
                </section>
              )}

              {selectedGap.related_paper_ids && selectedGap.related_paper_ids.length > 0 && (
                <section>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Related Literature</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedGap.related_paper_ids.map(id => (
                      <span key={id} className="text-xs font-medium bg-slate-100 text-slate-600 px-3 py-1.5 rounded-lg border border-slate-200">
                        Paper #{id}
                      </span>
                    ))}
                  </div>
                </section>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function RecentView({ recent, paper }) {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("newest");

  if (recent.length === 0) {
    return <EmptyState title="No Recent Research" description="No recent research was found within the configured research window." />;
  }

  let sortedRecent = [...recent];
  
  if (sort === "newest") sortedRecent.sort((a, b) => (b.year || 0) - (a.year || 0));
  if (sort === "oldest") sortedRecent.sort((a, b) => (a.year || 0) - (b.year || 0));
  if (sort === "relevance") sortedRecent.sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));
  
  const filteredRecent = sortedRecent.filter(r => 
    (r.title || "").toLowerCase().includes(search.toLowerCase()) || 
    (r.authors || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col md:flex-row gap-4 mb-2">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search recent research..." 
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-brand-500"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <select 
          className="p-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:border-brand-500"
          value={sort}
          onChange={e => setSort(e.target.value)}
        >
          <option value="newest">Newest First</option>
          <option value="oldest">Oldest First</option>
          <option value="relevance">Highest Relevance</option>
        </select>
      </div>

      <div className="relative border-l-2 border-slate-200 ml-4 pl-6 space-y-8">
        {filteredRecent.map((r, i) => (
          <div key={i} className="relative">
            <div className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-brand-500 ring-4 ring-white"></div>
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm transition-colors hover:border-brand-300">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="text-sm font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{r.year}</span>
                {r.addresses_gap && (
                  <Badge variant="warning" className="border-amber-200">Addresses Research Gap</Badge>
                )}
                {r.relationship_type && (
                  <Badge variant="default">{r.relationship_type}</Badge>
                )}
              </div>
              <h3 className="font-bold text-slate-900 mb-2 leading-snug pr-4">{r.title}</h3>
              <p className="text-sm text-slate-500 mb-4">{r.authors || "Unknown Authors"}</p>
              
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100">
                <div className="flex items-center gap-4">
                  {r.doi && (
                    <a href={`https://doi.org/${r.doi}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand-600 hover:text-brand-700 transition-colors">
                      Open Paper <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                  <a href={`/papers/${paper.id}/research/compare?papers=${r.id}`} className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors">
                    Compare With Target
                  </a>
                </div>
                <div className="text-xs font-semibold text-slate-400">
                  Rel: <span className="text-brand-600 font-bold">{r.relevance_score?.toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
