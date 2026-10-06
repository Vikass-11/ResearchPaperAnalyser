import { Link, useNavigate } from 'react-router-dom';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { FileText, ArrowRight, Upload, Search, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { papersApi } from '../api';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';

export function Dashboard() {
  const [data, setData] = useState({ papers: [], total: 0, loading: true, error: null });
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await papersApi.getPapers(1, 100);
        setData({ 
          papers: response.items || [], 
          total: response.total || 0, 
          loading: false, 
          error: null 
        });
      } catch (err) {
        setData(prev => ({ ...prev, loading: false, error: err.message || "Failed to load dashboard data" }));
      }
    };
    
    fetchDashboardData();
  }, []);

  if (data.loading) {
    return (
      <PageContainer title="Dashboard" subtitle="Welcome to ResearchPaperLens">
        <LoadingState message="Loading research library..." />
      </PageContainer>
    );
  }

  if (data.error) {
    return (
      <PageContainer title="Dashboard" subtitle="Welcome to ResearchPaperLens">
        <ErrorState title="Unable to load research library" message={data.error} onRetry={() => window.location.reload()} />
      </PageContainer>
    );
  }

  const completed = data.papers.filter(p => p.processing_status === "COMPLETED").length;
  const processing = data.papers.filter(p => p.processing_status === "PROCESSING" || p.processing_status === "ANALYZING" || p.processing_status === "PARSING").length;
  const failed = data.papers.filter(p => p.processing_status === "ERROR").length;

  const recentPapers = [...data.papers].sort((a, b) => b.id - a.id).slice(0, 5); // Assuming ID correlates with upload order.

  return (
    <PageContainer title="ScholarGraph AI" subtitle="Explore and analyze your research literature.">
      
      {/* Quick Actions */}
      <div className="flex flex-wrap gap-4 mb-8">
        <Button onClick={() => navigate('/upload')} icon={Upload} className="bg-brand-600 hover:bg-brand-700">Upload Research Paper</Button>
        <Button onClick={() => navigate('/papers')} variant="outline" icon={Search}>Browse Papers</Button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        <StatCard title="Total Papers" value={data.total} icon={FileText} color="blue" />
        <StatCard title="Processed" value={completed} icon={CheckCircle2} color="emerald" />
        <StatCard title="Processing" value={processing} icon={Clock} color="amber" />
        <StatCard title="Failed" value={failed} icon={AlertCircle} color="red" />
      </div>

      {/* Recent Research Papers */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900">Recent Research Papers</h3>
          <Link to="/papers" className="text-sm font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1">
            View All <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        
        {recentPapers.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-100">
              <FileText className="w-8 h-8 text-slate-400" />
            </div>
            <h4 className="text-slate-900 font-bold mb-2">Your research library is empty</h4>
            <p className="text-slate-500 text-sm mb-6 max-w-sm mx-auto">Upload your first research paper to begin building your research landscape.</p>
            <Button onClick={() => navigate('/upload')} icon={Upload}>Upload Research Paper</Button>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {recentPapers.map(paper => (
              <div key={paper.id} className="p-6 hover:bg-slate-50 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4 group">
                <div className="flex-1 min-w-0">
                  <h4 
                    onClick={() => navigate(`/papers/${paper.id}/research`)} 
                    className="text-base font-bold text-slate-900 mb-1 truncate cursor-pointer hover:text-brand-600 transition-colors"
                    title={paper.title}
                  >
                    {paper.title || "Untitled Paper"}
                  </h4>
                  <div className="flex items-center gap-3 text-xs text-slate-500 font-medium">
                    <span>{paper.year || "Unknown Year"}</span>
                    <span>•</span>
                    <span>Paper #{paper.id}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 shrink-0">
                  <StatusBadge status={paper.processing_status} />
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => navigate(`/papers/${paper.id}/research`)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    Open Workspace
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageContainer>
  );
}

function StatCard({ title, value, icon: Icon, color }) {
  const colorMap = {
    blue: "bg-blue-50 text-blue-600 border-blue-100",
    emerald: "bg-emerald-50 text-emerald-600 border-emerald-100",
    amber: "bg-amber-50 text-amber-600 border-amber-100",
    red: "bg-red-50 text-red-600 border-red-100",
  };

  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex items-center gap-5 transition-transform hover:-translate-y-1 duration-200">
      <div className={`p-4 rounded-xl border ${colorMap[color] || "bg-slate-50 text-slate-600 border-slate-100"}`}>
        <Icon className="w-6 h-6" strokeWidth={2.5} />
      </div>
      <div>
        <p className="text-2xl font-black text-slate-900 leading-none mb-1">{value}</p>
        <p className="text-xs font-bold text-slate-500 uppercase tracking-wider">{title}</p>
      </div>
    </div>
  );
}

export function StatusBadge({ status }) {
  const statusConfig = {
    "COMPLETED": { label: "✓ Completed", className: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    "PROCESSING": { label: "◌ Processing", className: "bg-amber-50 text-amber-700 border-amber-200" },
    "ANALYZING": { label: "◌ Analyzing", className: "bg-amber-50 text-amber-700 border-amber-200" },
    "PARSING": { label: "◌ Parsing", className: "bg-amber-50 text-amber-700 border-amber-200" },
    "UPLOADED": { label: "Pending", className: "bg-slate-50 text-slate-700 border-slate-200" },
    "ERROR": { label: "! Failed", className: "bg-red-50 text-red-700 border-red-200" },
  };

  const config = statusConfig[status?.toUpperCase()] || { label: status || "Unknown", className: "bg-slate-50 text-slate-700 border-slate-200" };

  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold border ${config.className}`}>
      {config.label}
    </span>
  );
}
