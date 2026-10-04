import { Link } from "react-router-dom";
import { ArrowLeft, Download, FileJson, FileText, File, Loader2 } from "lucide-react";
import { exportsApi } from "../../api/exports";
import { useState, useRef, useEffect } from "react";
import { useToast } from "../common/ToastContext";

export function ResearchHeader({ paper }) {
  const [showExports, setShowExports] = useState(false);
  const [exporting, setExporting] = useState(false);
  const { addToast } = useToast();
  const menuRef = useRef(null);

  const authors = paper.authors && paper.authors.length > 0 ? paper.authors.join(", ") : "Unknown Authors";
  const year = paper.year || "Unknown Year";

  // Handle click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowExports(false);
      }
    }
    if (showExports) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showExports]);

  // Handle escape key
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === "Escape" && showExports) {
        setShowExports(false);
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [showExports]);

  const handleExport = async (type) => {
    if (exporting) return;
    setExporting(true);
    setShowExports(false);
    try {
      if (type === 'json') await exportsApi.downloadJson(paper.id, paper.title);
      if (type === 'markdown') await exportsApi.downloadMarkdown(paper.id, paper.title);
      if (type === 'pdf') await exportsApi.downloadPdf(paper.id, paper.title);
      addToast(`${type.toUpperCase()} research report downloaded successfully.`, 'success');
    } catch (err) {
      addToast(err.message || 'Unable to export the research report.', 'error');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 print:hidden">
      <div>
        <Link to="/papers" className="inline-flex items-center text-sm font-medium text-slate-500 hover:text-brand-600 mb-3 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded">
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Papers
        </Link>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight leading-snug">{paper.title}</h1>
        <div className="flex flex-wrap items-center gap-2 mt-2 text-sm text-slate-500">
          <span>{authors}</span>
          <span className="w-1 h-1 rounded-full bg-slate-300"></span>
          <span>{year}</span>
        </div>
      </div>

      <div className="flex-shrink-0 relative" ref={menuRef}>
        <button 
          onClick={() => setShowExports(!showExports)}
          disabled={exporting}
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          aria-expanded={showExports}
          aria-haspopup="true"
        >
          {exporting ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Exporting...</>
          ) : (
            <><Download className="w-4 h-4" /> Export</>
          )}
        </button>
        
        {showExports && (
          <div 
            className="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-slate-200 z-50 overflow-hidden animate-fade-in"
            role="menu"
          >
            <button 
              onClick={() => handleExport('json')} 
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 text-sm font-medium text-slate-700 transition-colors focus-visible:outline-none focus-visible:bg-slate-50"
              role="menuitem"
            >
              <FileJson className="w-4 h-4 text-blue-500" /> JSON Export
            </button>
            <button 
              onClick={() => handleExport('markdown')} 
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 text-sm font-medium text-slate-700 transition-colors border-t border-slate-100 focus-visible:outline-none focus-visible:bg-slate-50"
              role="menuitem"
            >
              <FileText className="w-4 h-4 text-emerald-500" /> Markdown Export
            </button>
            <button 
              onClick={() => handleExport('pdf')} 
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 text-sm font-medium text-slate-700 transition-colors border-t border-slate-100 focus-visible:outline-none focus-visible:bg-slate-50"
              role="menuitem"
            >
              <File className="w-4 h-4 text-rose-500" /> PDF Report
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
