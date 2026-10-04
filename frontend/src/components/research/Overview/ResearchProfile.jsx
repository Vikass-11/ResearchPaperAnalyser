import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { literatureApi } from "../../../api";
import { LoadingState } from "../../common/LoadingState";
import { ErrorState } from "../../common/ErrorState";
import { Badge } from "../../common/Badge";
import { EmptyState } from "../../common/EmptyState";
import { Target, Layers, Layout, FileText, Database } from "lucide-react";

export function ResearchProfile() {
  const { paper } = useOutletContext();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!paper) return;
    
    const fetchProfile = async () => {
      try {
        const data = await literatureApi.getResearchProfile(paper.id);
        setProfile(data.research_profile || data);
        setError(null);
      } catch (err) {
        if (err.code === "PROFILE_NOT_FOUND" || err.status === 404) {
           // Not an error, just empty
           setProfile(null);
        } else {
           setError(err.message || "Failed to load research profile.");
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchProfile();
  }, [paper]);

  if (loading) return <LoadingState message="Loading research profile..." />;
  if (error) return <ErrorState title="Profile Unavailable" message={error} />;
  if (!profile) return <EmptyState title="Profile Not Generated" description="The research profile for this paper has not been generated yet." icon={FileText} />;

  const arrayFields = [
    { label: "Sub-domains", values: profile.sub_domains },
    { label: "Methods", values: profile.methods },
    { label: "Algorithms", values: profile.algorithms },
    { label: "Models", values: profile.models },
    { label: "Technologies", values: profile.technologies },
    { label: "Datasets", values: profile.datasets },
    { label: "Key Concepts", values: profile.key_concepts },
    { label: "Keywords", values: profile.keywords },
  ];

  return (
    <div className="flex flex-col gap-8 animate-fade-in">
      
      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <Target className="w-5 h-5 text-brand-600" /> Core Focus
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">Research Domain</h3>
            <p className="text-lg font-medium text-slate-900 bg-slate-50 p-4 rounded-xl border border-slate-100">{profile.research_domain || "Not specified"}</p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">Application Domain</h3>
            <p className="text-lg font-medium text-slate-900 bg-slate-50 p-4 rounded-xl border border-slate-100">{profile.application_domain || "Not specified"}</p>
          </div>
        </div>

        <div className="mt-8 space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">Research Topic</h3>
            <p className="text-base text-slate-800">{profile.research_topic || "Not specified"}</p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">Research Problem</h3>
            <p className="text-base text-slate-800">{profile.research_problem || "Not specified"}</p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">Objective</h3>
            <p className="text-base text-slate-800">{profile.research_objective || "Not specified"}</p>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">Methodology Overview</h3>
            <p className="text-base text-slate-800">{profile.methodology || "Not specified"}</p>
          </div>
        </div>
      </div>

      <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <Layers className="w-5 h-5 text-brand-600" /> Attributes & Components
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
          {arrayFields.map((field) => (
            field.values && field.values.length > 0 ? (
              <div key={field.label}>
                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">{field.label}</h3>
                <div className="flex flex-wrap gap-2">
                  {field.values.map((v, i) => (
                    <Badge key={i} variant="default">{v}</Badge>
                  ))}
                </div>
              </div>
            ) : null
          ))}
        </div>
      </div>

      {profile.research_questions && profile.research_questions.length > 0 && (
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
          <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
            <Layout className="w-5 h-5 text-brand-600" /> Research Questions
          </h2>
          <div className="space-y-4">
            {profile.research_questions.map((q, i) => (
              <div key={i} className="flex gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-brand-600 font-bold font-mono text-lg opacity-50 pt-0.5">{(i+1).toString().padStart(2, '0')}</span>
                <p className="text-slate-800 font-medium">{q}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      
    </div>
  );
}
