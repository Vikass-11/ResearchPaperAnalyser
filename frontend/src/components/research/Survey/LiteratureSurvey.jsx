import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { literatureApi } from "../../../api";
import { LoadingState } from "../../common/LoadingState";
import { ErrorState } from "../../common/ErrorState";
import { EmptyState } from "../../common/EmptyState";
import { BookOpen } from "lucide-react";

export function LiteratureSurvey() {
  const { paper } = useOutletContext();
  const [survey, setSurvey] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!paper) return;
    
    const fetchSurvey = async () => {
      try {
        const data = await literatureApi.getLiteratureSurvey(paper.id);
        setSurvey(data);
        setError(null);
      } catch (err) {
        if (err.status === 404) {
           setSurvey(null);
        } else {
           setError(err.message || "Failed to load literature survey.");
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchSurvey();
  }, [paper]);

  if (loading) return <LoadingState message="Loading literature survey..." />;
  if (error) return <ErrorState title="Survey Unavailable" message={error} />;
  if (!survey) return <EmptyState title="Survey Not Synthesized" description="A comprehensive literature survey has not been synthesized for this paper yet." icon={BookOpen} />;

  const sections = [
    { key: "research_context", title: "Research Context" },
    { key: "research_landscape", title: "Research Landscape" },
    { key: "themes", title: "Major Themes", isList: true },
    { key: "methodological_comparison", title: "Methodological Comparison" },
    { key: "findings_synthesis", title: "Findings Synthesis" },
    { key: "research_evolution", title: "Research Evolution" },
    { key: "target_comparison", title: "Target Comparison" },
    { key: "overall_synthesis", title: "Overall Synthesis" }
  ];

  return (
    <div className="flex flex-col gap-8 animate-fade-in max-w-4xl mx-auto">
      <div className="text-center mb-4">
        <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight mb-3">Literature Survey</h2>
        <p className="text-lg text-slate-500">Comprehensive synthesis of related research</p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        {sections.map(({ key, title, isList }) => {
          const content = survey[key];
          if (!content || (isList && content.length === 0)) return null;

          return (
            <div key={key} className="p-8 border-b border-slate-100 last:border-b-0">
              <h3 className="text-xl font-bold text-slate-900 mb-6">{title}</h3>
              
              {isList ? (
                <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {content.map((theme, i) => (
                    <li key={i} className="flex gap-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
                      <span className="text-brand-600 font-bold font-mono opacity-50 pt-0.5">{(i+1).toString().padStart(2, '0')}</span>
                      <span className="text-slate-700 font-medium">{theme}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="prose prose-slate max-w-none text-slate-700 leading-loose">
                  {content.split('\n').map((paragraph, idx) => (
                    paragraph.trim() ? <p key={idx}>{paragraph}</p> : null
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
