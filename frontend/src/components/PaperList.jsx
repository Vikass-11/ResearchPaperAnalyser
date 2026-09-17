import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FileText, ChevronRight, Clock, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

export default function PaperList({ refreshTrigger }) {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchPapers = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/papers/");
      const data = await res.json();
      setPapers(data);
    } catch (err) {
      console.error("Failed to fetch papers:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPapers();
    // Setup polling for processing status
    const interval = setInterval(() => {
      fetchPapers();
    }, 5000);
    return () => clearInterval(interval);
  }, [refreshTrigger]);

  if (loading && papers.length === 0) {
    return (
      <div className="glass-card p-12 rounded-2xl flex flex-col items-center justify-center text-slate-500">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500 mb-3" />
        <p>Loading your library...</p>
      </div>
    );
  }

  if (papers.length === 0) {
    return (
      <div className="glass-card p-12 rounded-2xl flex flex-col items-center justify-center text-slate-500 border-dashed border-2">
        <div className="bg-slate-100 p-4 rounded-full mb-3">
          <FileText className="w-8 h-8 text-slate-400" />
        </div>
        <p className="font-medium text-slate-700">No papers uploaded yet</p>
        <p className="text-sm mt-1">Upload a PDF to get started with analysis.</p>
      </div>
    );
  }

  const getStatusDisplay = (status) => {
    switch(status) {
      case 'COMPLETED':
        return <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200"><CheckCircle2 className="w-3.5 h-3.5" /> Ready</span>;
      case 'ERROR':
        return <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-rose-50 text-rose-700 border border-rose-200"><AlertCircle className="w-3.5 h-3.5" /> Failed</span>;
      default:
        return <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full bg-amber-50 text-amber-700 border border-amber-200"><Loader2 className="w-3.5 h-3.5 animate-spin" /> {status}</span>;
    }
  };

  return (
    <div className="glass-card rounded-2xl overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200/60">
          <thead className="bg-slate-50/50">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Document Title</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Date Added</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white/40">
            {papers.map((paper) => (
              <tr 
                key={paper.id} 
                onClick={() => navigate(`/paper/${paper.id}`)} 
                className="hover:bg-brand-50/40 cursor-pointer transition-colors group"
              >
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-100 rounded-lg text-slate-500 group-hover:bg-brand-100 group-hover:text-brand-600 transition-colors">
                      <FileText className="w-5 h-5" />
                    </div>
                    <span className="text-sm font-semibold text-slate-900 line-clamp-1">{paper.title}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusDisplay(paper.processing_status)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-1.5 text-sm text-slate-500">
                    <Clock className="w-4 h-4" />
                    {new Date(paper.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <div className="inline-flex items-center justify-center p-1.5 rounded-full text-slate-400 group-hover:text-brand-600 group-hover:bg-brand-50 transition-colors">
                    <ChevronRight className="w-5 h-5" />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
