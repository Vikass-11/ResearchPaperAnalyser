import { useEffect, useState, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { FileText, ChevronRight, CheckCircle2, AlertCircle, Loader2, Search, X, Trash2, Filter, ChevronLeft } from "lucide-react";
import { papersApi } from "../api";
import { Button } from "./common/Button";

export default function PaperList() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // Read URL State
  const searchQuery = searchParams.get("search") || "";
  const filterStatus = searchParams.get("status") || "ALL";
  const filterYear = searchParams.get("year") || "ALL";
  const sortBy = searchParams.get("sort") || "newest";
  const currentPage = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = 10;

  const fetchPapers = async () => {
    try {
      setLoading(true);
      const data = await papersApi.getPapers(1, 100);
      setPapers(data.items || []);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch papers:", err);
      setError("Failed to load research library.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPapers();
    const interval = setInterval(() => {
      setPapers(current => {
        if (current.some(p => ["PROCESSING", "ANALYZING", "PARSING", "UPLOADED"].includes(p.processing_status))) {
          fetchPapers();
        }
        return current;
      });
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Handle escape key
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === "Escape" && deleteConfirm) {
        setDeleteConfirm(null);
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [deleteConfirm]);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (deleteLoading) return;
    setDeleteLoading(true);
    try {
      await papersApi.deletePaper(id);
      setDeleteConfirm(null);
      fetchPapers(); // Refresh
    } catch (err) {
      alert("Failed to delete paper.");
    } finally {
      setDeleteLoading(false);
    }
  };

  // Derived filters
  const availableYears = [...new Set(papers.map(p => p.year).filter(Boolean))].sort((a, b) => b - a);

  // Apply filters and sort locally
  const processedPapers = useMemo(() => {
    let result = [...papers];

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(p => (p.title || "").toLowerCase().includes(q));
    }

    if (filterStatus !== "ALL") {
      result = result.filter(p => p.processing_status === filterStatus);
    }

    if (filterYear !== "ALL") {
      result = result.filter(p => p.year === parseInt(filterYear, 10));
    }

    if (sortBy === "newest") {
      result.sort((a, b) => b.id - a.id);
    } else if (sortBy === "oldest") {
      result.sort((a, b) => a.id - b.id);
    } else if (sortBy === "title-asc") {
      result.sort((a, b) => (a.title || "").localeCompare(b.title || ""));
    } else if (sortBy === "title-desc") {
      result.sort((a, b) => (b.title || "").localeCompare(a.title || ""));
    }

    return result;
  }, [papers, searchQuery, filterStatus, filterYear, sortBy]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(processedPapers.length / pageSize));
  const validPage = Math.min(Math.max(1, currentPage), totalPages);
  
  const paginatedPapers = processedPapers.slice((validPage - 1) * pageSize, validPage * pageSize);

  const updateParams = (updates) => {
    const newParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, value]) => {
      if (value === null || value === "ALL" || value === "") {
        newParams.delete(key);
      } else {
        newParams.set(key, value);
      }
    });
    // Reset to page 1 if search/filter/sort changes
    if (!updates.page && (updates.search !== undefined || updates.status !== undefined || updates.year !== undefined || updates.sort !== undefined)) {
      newParams.delete("page");
    }
    setSearchParams(newParams);
  };

  const clearFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  const getStatusDisplay = (status) => {
    switch(status) {
      case 'COMPLETED':
        return <span className="flex items-center gap-1.5 w-max px-2.5 py-1 text-xs font-medium rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200"><CheckCircle2 className="w-3.5 h-3.5" /> Completed</span>;
      case 'ERROR':
        return <span className="flex items-center gap-1.5 w-max px-2.5 py-1 text-xs font-medium rounded-md bg-rose-50 text-rose-700 border border-rose-200"><AlertCircle className="w-3.5 h-3.5" /> Failed</span>;
      default:
        return <span className="flex items-center gap-1.5 w-max px-2.5 py-1 text-xs font-medium rounded-md bg-amber-50 text-amber-700 border border-amber-200"><Loader2 className="w-3.5 h-3.5 animate-spin" /> Processing</span>;
    }
  };

  if (loading && papers.length === 0) {
    return (
      <div className="p-12 flex flex-col items-center justify-center text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500 mb-3" />
        <p>Loading research library...</p>
      </div>
    );
  }

  if (error && papers.length === 0) {
    return (
      <div className="p-12 flex flex-col items-center justify-center text-slate-500">
        <AlertCircle className="w-8 h-8 text-red-500 mb-3" />
        <p>{error}</p>
        <Button onClick={fetchPapers} className="mt-4">Retry</Button>
      </div>
    );
  }

  if (papers.length === 0) {
    return (
      <div className="p-16 flex flex-col items-center justify-center text-slate-500 text-center">
        <div className="bg-slate-100 p-4 rounded-full mb-4">
          <FileText className="w-10 h-10 text-slate-400" />
        </div>
        <h3 className="text-lg font-bold text-slate-900 mb-2">Your research library is empty</h3>
        <p className="text-sm max-w-md mx-auto mb-6">Upload your first research paper to begin extracting methodology, literature context, and research gaps.</p>
        <Button onClick={() => navigate('/upload')}>Upload Research Paper</Button>
      </div>
    );
  }

  const hasActiveFilters = searchQuery || filterStatus !== "ALL" || filterYear !== "ALL";

  return (
    <div className="flex flex-col gap-6">
      
      {/* Search & Filters Bar */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <label htmlFor="search" className="sr-only">Search papers</label>
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input 
            id="search"
            type="text" 
            placeholder="Search papers by title..." 
            className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
            value={searchQuery}
            onChange={e => updateParams({ search: e.target.value })}
          />
        </div>
        
        <div className="flex flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="status" className="text-xs font-bold text-slate-500 uppercase tracking-wider">Status</label>
            <select 
              id="status"
              className="p-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:border-brand-500"
              value={filterStatus}
              onChange={e => updateParams({ status: e.target.value })}
            >
              <option value="ALL">All</option>
              <option value="COMPLETED">Completed</option>
              <option value="PROCESSING">Processing</option>
              <option value="ERROR">Failed</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="year" className="text-xs font-bold text-slate-500 uppercase tracking-wider">Year</label>
            <select 
              id="year"
              className="p-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:border-brand-500"
              value={filterYear}
              onChange={e => updateParams({ year: e.target.value })}
            >
              <option value="ALL">All Years</option>
              {availableYears.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="sort" className="text-xs font-bold text-slate-500 uppercase tracking-wider">Sort</label>
            <select 
              id="sort"
              className="p-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:border-brand-500"
              value={sortBy}
              onChange={e => updateParams({ sort: e.target.value })}
            >
              <option value="newest">Newest ↓</option>
              <option value="oldest">Oldest ↑</option>
              <option value="title-asc">Title A–Z</option>
              <option value="title-desc">Title Z–A</option>
            </select>
          </div>
        </div>
      </div>

      {/* Active Filters */}
      {hasActiveFilters && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-500 font-medium mr-2">Active Filters:</span>
          {searchQuery && (
            <span className="inline-flex items-center gap-1 bg-brand-50 text-brand-700 px-3 py-1 rounded-full border border-brand-100">
              Search: {searchQuery}
              <button onClick={() => updateParams({ search: null })} className="hover:text-brand-900" aria-label="Remove search filter"><X className="w-3 h-3" /></button>
            </span>
          )}
          {filterStatus !== "ALL" && (
            <span className="inline-flex items-center gap-1 bg-brand-50 text-brand-700 px-3 py-1 rounded-full border border-brand-100">
              Status: {filterStatus}
              <button onClick={() => updateParams({ status: null })} className="hover:text-brand-900" aria-label="Remove status filter"><X className="w-3 h-3" /></button>
            </span>
          )}
          {filterYear !== "ALL" && (
            <span className="inline-flex items-center gap-1 bg-brand-50 text-brand-700 px-3 py-1 rounded-full border border-brand-100">
              Year: {filterYear}
              <button onClick={() => updateParams({ year: null })} className="hover:text-brand-900" aria-label="Remove year filter"><X className="w-3 h-3" /></button>
            </span>
          )}
          <button onClick={clearFilters} className="text-sm font-semibold text-slate-500 hover:text-slate-700 underline ml-2">
            Clear All
          </button>
        </div>
      )}

      {/* Paper Table */}
      {processedPapers.length === 0 ? (
        <div className="p-12 text-center border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50">
          <Search className="w-8 h-8 text-slate-400 mx-auto mb-3" />
          <h3 className="font-bold text-slate-900 mb-2">No research papers match your filters.</h3>
          <p className="text-slate-500 text-sm mb-4">Try changing your search or clearing some filters.</p>
          <Button onClick={clearFilters} variant="outline">Clear Filters</Button>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-sm custom-scrollbar">
          <table className="min-w-full text-left border-collapse bg-white">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th scope="col" className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Document Title</th>
                <th scope="col" className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider w-32">Year</th>
                <th scope="col" className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider w-40">Status</th>
                <th scope="col" className="px-6 py-4 text-right text-xs font-bold text-slate-500 uppercase tracking-wider w-24">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {paginatedPapers.map((paper) => (
                <tr 
                  key={paper.id} 
                  onClick={() => navigate(`/papers/${paper.id}/research`)} 
                  className="hover:bg-slate-50 cursor-pointer transition-colors group"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-4">
                      <div className="p-2.5 bg-slate-100 rounded-xl text-slate-400 group-hover:bg-brand-100 group-hover:text-brand-600 transition-colors shrink-0">
                        <FileText className="w-5 h-5" />
                      </div>
                      <span className="text-sm font-bold text-slate-900 group-hover:text-brand-700 transition-colors line-clamp-2 pr-4">{paper.title || "Untitled Paper"}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-medium text-slate-600 bg-slate-100 px-2 py-1 rounded-md">{paper.year || "N/A"}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusDisplay(paper.processing_status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex justify-end gap-2">
                      {deleteConfirm === paper.id ? (
                        <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                          <button 
                            onClick={(e) => handleDelete(e, paper.id)} 
                            disabled={deleteLoading}
                            className="text-xs font-bold text-white bg-red-600 px-3 py-1.5 rounded-lg hover:bg-red-700 disabled:opacity-50"
                          >
                            {deleteLoading ? "Deleting..." : "Confirm"}
                          </button>
                          <button 
                            onClick={() => setDeleteConfirm(null)} 
                            disabled={deleteLoading}
                            className="text-xs font-bold text-slate-600 bg-slate-100 px-3 py-1.5 rounded-lg hover:bg-slate-200 disabled:opacity-50"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <>
                          <button 
                            onClick={(e) => { e.stopPropagation(); setDeleteConfirm(paper.id); }} 
                            className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                            aria-label={`Delete ${paper.title}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                          <div className="p-2 text-slate-400 group-hover:text-brand-600 group-hover:bg-brand-50 rounded-lg transition-colors">
                            <ChevronRight className="w-4 h-4" />
                          </div>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-4 border-t border-slate-200">
          <div className="text-sm text-slate-500">
            Showing <span className="font-semibold text-slate-900">{(validPage - 1) * pageSize + 1}</span> to <span className="font-semibold text-slate-900">{Math.min(validPage * pageSize, processedPapers.length)}</span> of <span className="font-semibold text-slate-900">{processedPapers.length}</span> papers
          </div>
          <div className="flex items-center gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => updateParams({ page: validPage - 1 })}
              disabled={validPage === 1}
            >
              <ChevronLeft className="w-4 h-4 mr-1" /> Previous
            </Button>
            <div className="flex items-center gap-1">
              {[...Array(totalPages)].map((_, i) => (
                <button
                  key={i}
                  onClick={() => updateParams({ page: i + 1 })}
                  className={`w-8 h-8 flex items-center justify-center rounded-lg text-sm font-semibold transition-colors ${validPage === i + 1 ? 'bg-brand-600 text-white' : 'text-slate-600 hover:bg-slate-100'}`}
                  aria-label={`Page ${i + 1}`}
                  aria-current={validPage === i + 1 ? "page" : undefined}
                >
                  {i + 1}
                </button>
              ))}
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => updateParams({ page: validPage + 1 })}
              disabled={validPage === totalPages}
            >
              Next <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
