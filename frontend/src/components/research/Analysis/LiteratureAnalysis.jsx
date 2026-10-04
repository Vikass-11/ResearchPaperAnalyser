import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { literatureApi } from "../../../api";
import { LoadingState } from "../../common/LoadingState";
import { ErrorState } from "../../common/ErrorState";
import { EmptyState } from "../../common/EmptyState";
import { FileSearch, Target, PenTool, Database, Lightbulb, AlertTriangle, TrendingUp } from "lucide-react";

export function LiteratureAnalysis() {
  const { paper } = useOutletContext();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!paper) return;
    
    const fetchAnalysis = async () => {
      try {
        const data = await literatureApi.getLiteratureAnalysis(paper.id);
        // data should be an array of analyses based on backend structure
        setAnalyses(data || []);
        setError(null);
      } catch (err) {
        if (err.status === 404) {
           setAnalyses([]);
        } else {
           setError(err.message || "Failed to load literature analysis.");
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalysis();
  }, [paper]);

  if (loading) return <LoadingState message="Loading literature analysis..." />;
  if (error) return <ErrorState title="Analysis Unavailable" message={error} />;
  if (analyses.length === 0) return <EmptyState title="No Analysis Available" description="Detailed analysis has not been generated for the related literature yet." icon={FileSearch} />;

  return (
    <div className="flex flex-col gap-8 animate-fade-in">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-xl font-bold text-slate-900">Detailed Paper Analysis</h2>
        <span className="text-sm font-medium text-slate-500 bg-slate-100 px-3 py-1 rounded-full">{analyses.length} Papers Analyzed</span>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {analyses.map((analysis) => (
          <AnalysisCard key={analysis.id} analysis={analysis} />
        ))}
      </div>
    </div>
  );
}

const Section = ({ title, icon: Icon, children }) => {
  if (!children) return null;
  return (
    <div className="mb-6 last:mb-0">
      <h4 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-2">
        {Icon && <Icon className="w-4 h-4 text-brand-500" />}
        {title}
      </h4>
      <div className="text-slate-600 text-sm leading-relaxed bg-slate-50/50 p-4 rounded-xl border border-slate-100">
        {children}
      </div>
    </div>
  );
};

const ListSection = ({ title, icon: Icon, items }) => {
  if (!items || items.length === 0) return null;
  return (
    <div className="mb-6 last:mb-0">
      <h4 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-2">
        {Icon && <Icon className="w-4 h-4 text-brand-500" />}
        {title}
      </h4>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex gap-3 text-sm text-slate-600">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-400 flex-shrink-0 mt-1.5"></span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

function AnalysisCard({ analysis }) {
  return (
    <div className="bg-white p-6 md:p-8 rounded-2xl shadow-sm border border-slate-200">
      <div className="mb-8 border-b border-slate-100 pb-6">
        <h3 className="text-lg font-bold text-slate-900 leading-snug">
          {analysis.related_paper?.title || "Unknown Paper"}
        </h3>
        <p className="text-sm text-slate-500 mt-2">
          {analysis.related_paper?.authors} • {analysis.related_paper?.year}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-12 gap-y-2">
        <div>
          <Section title="Problem Statement" icon={Target}>{analysis.problem_statement}</Section>
          <Section title="Objective" icon={Target}>{analysis.objective}</Section>
          <Section title="Methodology" icon={PenTool}>{analysis.methodology}</Section>
          <Section title="Datasets / Setup" icon={Database}>
            {analysis.datasets || analysis.experimental_setup || "Not specified"}
          </Section>
        </div>

        <div>
          <ListSection title="Key Findings" icon={Lightbulb} items={analysis.key_findings} />
          <ListSection title="Contributions" icon={TrendingUp} items={analysis.contributions} />
          <ListSection title="Limitations" icon={AlertTriangle} items={analysis.limitations} />
          
          {(analysis.similarities?.length > 0 || analysis.differences?.length > 0) && (
            <div className="mt-8 bg-brand-50 border border-brand-100 p-5 rounded-xl">
              <h4 className="text-sm font-bold text-brand-800 uppercase tracking-wider mb-4">Comparison to Target Paper</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <h5 className="text-xs font-bold text-brand-600 mb-2 uppercase">Similarities</h5>
                  <ul className="space-y-1">
                    {analysis.similarities?.map((s, i) => (
                      <li key={i} className="text-xs text-brand-700 flex gap-2"><span>•</span><span>{s}</span></li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h5 className="text-xs font-bold text-brand-600 mb-2 uppercase">Differences</h5>
                  <ul className="space-y-1">
                    {analysis.differences?.map((d, i) => (
                      <li key={i} className="text-xs text-brand-700 flex gap-2"><span>•</span><span>{d}</span></li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
