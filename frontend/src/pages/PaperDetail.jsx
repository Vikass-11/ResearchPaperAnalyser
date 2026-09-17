import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, BookOpen, Layers, CheckCircle, FileText, AlertTriangle, List, Network } from "lucide-react";
import CitationGraph from "../components/CitationGraph";
export default function PaperDetail() {
  const { id } = useParams();
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState("ai_summary"); // Tab state

  useEffect(() => {
    const fetchPaper = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/papers/${id}`);
        const data = await res.json();
        setPaper(data);
      } catch (err) {
        console.error("Failed to fetch paper:", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchPaper();
    const interval = setInterval(() => {
      if (paper && ["UPLOADED", "PARSING", "ANALYZING"].includes(paper.processing_status)) {
        fetchPaper();
      }
    }, 3000);
    
    return () => clearInterval(interval);
  }, [id, paper?.processing_status]);

  if (loading) return <div className="p-8 text-center text-slate-500">Loading paper details...</div>;
  if (!paper) return <div className="p-8 text-center text-red-500">Paper not found.</div>;

  const isProcessing = ["UPLOADED", "PARSING", "ANALYZING"].includes(paper.processing_status);

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4 bg-white/40 backdrop-blur-sm p-4 rounded-2xl border border-white/60 shadow-sm">
        <Link to="/" className="p-2 bg-white hover:bg-brand-50 text-slate-600 hover:text-brand-600 rounded-full transition-all shadow-sm border border-slate-100">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{paper.title}</h1>
          <p className="text-sm text-slate-500 mt-1">
            {paper.authors && paper.authors.length > 0 ? paper.authors.join(", ") : "Unknown Authors"} • {paper.year || "Unknown Year"}
          </p>
        </div>
      </div>

      {isProcessing && (
        <div className="bg-yellow-50 border border-yellow-200 p-6 rounded-lg text-yellow-800 flex items-center gap-4 shadow-sm">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-yellow-800"></div>
          <div>
            <p className="font-semibold text-lg">AI is processing this paper...</p>
            <p className="text-sm mt-1">Current Task: {paper.processing_status}. This usually takes 30-60 seconds depending on the model.</p>
          </div>
        </div>
      )}

      {paper.processing_status === "ERROR" && (
        <div className="bg-red-50 border border-red-200 p-6 rounded-lg text-red-800 flex items-center gap-4 shadow-sm">
          <AlertTriangle className="w-6 h-6" />
          <div>
            <p className="font-semibold text-lg">Processing Failed</p>
            <p className="text-sm mt-1">{paper.error_message}</p>
          </div>
        </div>
      )}

      {paper.processing_status === "COMPLETED" && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Sidebar Nav */}
          <div className="lg:col-span-1 flex flex-col gap-2 glass-card p-4 rounded-2xl h-fit sticky top-24">
            <button 
              onClick={() => setActiveSection("ai_summary")}
              className={`text-left px-4 py-3 rounded-xl flex items-center gap-3 transition-all ${activeSection === "ai_summary" ? "bg-brand-50 text-brand-700 font-semibold shadow-sm border border-brand-100 translate-x-1" : "hover:bg-slate-50 text-slate-600 hover:text-slate-900 border border-transparent font-medium"}`}>
              <BookOpen className={`w-4 h-4 ${activeSection === "ai_summary" ? "text-brand-600" : ""}`} /> AI Summary & Insights
            </button>
            <button 
              onClick={() => setActiveSection("methodology")}
              className={`text-left px-4 py-3 rounded-xl flex items-center gap-3 transition-all ${activeSection === "methodology" ? "bg-brand-50 text-brand-700 font-semibold shadow-sm border border-brand-100 translate-x-1" : "hover:bg-slate-50 text-slate-600 hover:text-slate-900 border border-transparent font-medium"}`}>
              <Layers className={`w-4 h-4 ${activeSection === "methodology" ? "text-brand-600" : ""}`} /> Methodology & Results
            </button>
            <button 
              onClick={() => setActiveSection("extracted")}
              className={`text-left px-4 py-3 rounded-xl flex items-center gap-3 transition-all ${activeSection === "extracted" ? "bg-brand-50 text-brand-700 font-semibold shadow-sm border border-brand-100 translate-x-1" : "hover:bg-slate-50 text-slate-600 hover:text-slate-900 border border-transparent font-medium"}`}>
              <FileText className={`w-4 h-4 ${activeSection === "extracted" ? "text-brand-600" : ""}`} /> Extracted Sections
            </button>
            <button 
              onClick={() => setActiveSection("references")}
              className={`text-left px-4 py-3 rounded-xl flex items-center gap-3 transition-all ${activeSection === "references" ? "bg-brand-50 text-brand-700 font-semibold shadow-sm border border-brand-100 translate-x-1" : "hover:bg-slate-50 text-slate-600 hover:text-slate-900 border border-transparent font-medium"}`}>
              <List className={`w-4 h-4 ${activeSection === "references" ? "text-brand-600" : ""}`} /> References
            </button>
            <button 
              onClick={() => setActiveSection("graph")}
              className={`text-left px-4 py-3 rounded-xl flex items-center gap-3 transition-all ${activeSection === "graph" ? "bg-brand-50 text-brand-700 font-semibold shadow-sm border border-brand-100 translate-x-1" : "hover:bg-slate-50 text-slate-600 hover:text-slate-900 border border-transparent font-medium"}`}>
              <Network className={`w-4 h-4 ${activeSection === "graph" ? "text-brand-600" : ""}`} /> Citation Graph
            </button>
          </div>

          {/* Content Area */}
          <div className="lg:col-span-3 min-h-[600px]">
            
            {activeSection === "ai_summary" && (
              <div className="flex flex-col gap-6 animate-slide-up">
                <div className="glass-card p-8 rounded-2xl">
                  <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2 border-b border-slate-100 pb-3">Executive Summary</h3>
                  <p className="text-slate-600 whitespace-pre-wrap leading-relaxed">{paper.summary}</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="glass-card p-8 rounded-2xl">
                    <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2 border-b border-slate-100 pb-3">
                      <CheckCircle className="w-5 h-5 text-emerald-500" /> Key Contributions
                    </h3>
                    <ul className="list-disc list-inside text-slate-600 space-y-3">
                      {paper.contributions?.map((c, i) => <li key={i} className="pl-1">{c}</li>)}
                    </ul>
                  </div>
                  
                  <div className="glass-card p-8 rounded-2xl">
                    <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2 border-b border-slate-100 pb-3">Core Problem</h3>
                    <p className="text-slate-600 leading-relaxed">{paper.problem_statement}</p>
                  </div>
                </div>
              </div>
            )}

            {activeSection === "methodology" && (
              <div className="flex flex-col gap-6 animate-slide-up">
                <div className="glass-card p-8 rounded-2xl">
                  <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2 border-b border-slate-100 pb-3">Methodology</h3>
                  <p className="text-slate-600 whitespace-pre-wrap leading-relaxed">{paper.methodology}</p>
                </div>
                <div className="glass-card p-8 rounded-2xl">
                  <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2 border-b border-slate-100 pb-3">Results & Findings</h3>
                  <ul className="list-disc list-inside text-slate-600 space-y-3">
                    {paper.results?.map((r, i) => <li key={i} className="leading-relaxed pl-1">{r}</li>)}
                  </ul>
                </div>
              </div>
            )}

            {activeSection === "extracted" && (
              <div className="flex flex-col gap-4 animate-slide-up">
                <div className="flex items-center justify-between mb-2">
                   <h3 className="text-xl font-bold text-slate-800">Raw Extracted Sections</h3>
                   <span className="text-xs bg-slate-200/50 text-slate-600 font-medium px-3 py-1 rounded-full border border-slate-200">via GROBID TEI</span>
                </div>
                {paper.sections?.length > 0 ? paper.sections.map(sec => (
                  <div key={sec.id} className="glass-card p-6 rounded-xl">
                    <h4 className="font-semibold text-slate-900 mb-3 border-b border-slate-100 pb-2">{sec.section_name}</h4>
                    <p className="text-sm text-slate-600 whitespace-pre-wrap leading-relaxed line-clamp-3 hover:line-clamp-none transition-all cursor-pointer" title="Click to expand">
                      {sec.content}
                    </p>
                  </div>
                )) : <p className="text-slate-500 italic p-6 glass-card rounded-xl">No sections could be cleanly extracted.</p>}
              </div>
            )}
            
            {activeSection === "references" && (
              <div className="flex flex-col gap-4 animate-slide-up">
                <div className="flex items-center justify-between mb-2">
                   <h3 className="text-xl font-bold text-slate-800">References</h3>
                   <span className="text-xs bg-brand-50 text-brand-700 font-semibold px-3 py-1 rounded-full border border-brand-100">{paper.references?.length || 0} extracted</span>
                </div>
                {paper.references?.length > 0 ? paper.references.map(ref => (
                  <div key={ref.id} className="glass-card p-6 rounded-xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-brand-400 opacity-50"></div>
                    <div className="font-semibold text-slate-900 mb-1">{ref.title}</div>
                    <div className="text-sm text-slate-600 mb-2 font-medium">
                      {ref.authors?.join(", ")} {ref.year ? `(${ref.year})` : ""}
                      {ref.journal_conference ? ` - ${ref.journal_conference}` : ""}
                    </div>
                    {ref.citations?.length > 0 && (
                      <div className="mt-4 bg-slate-50/80 p-4 rounded-lg text-sm text-slate-700 border border-slate-100">
                        <div className="font-semibold mb-2 flex items-center gap-2 text-slate-800"><List className="w-4 h-4 text-brand-500" /> Cited in text:</div>
                        <ul className="list-disc list-inside space-y-1.5 ml-1">
                          {ref.citations.map(cit => (
                            <li key={cit.id}><span className="text-brand-600 font-medium">[{cit.section_name}]</span> <span className="text-slate-600">{cit.context}</span></li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )) : <p className="text-slate-500 italic p-6 glass-card rounded-xl">No references could be cleanly extracted.</p>}
              </div>
            )}
            
            {activeSection === "graph" && (
              <div className="flex flex-col gap-4 w-full h-full animate-slide-up">
                <div className="flex items-center justify-between mb-2">
                   <h3 className="text-xl font-bold text-slate-800">Citation Relationship Graph</h3>
                </div>
                <div className="glass-card p-2 rounded-2xl">
                  <CitationGraph paperId={paper.id} />
                </div>
              </div>
            )}

          </div>
        </div>
      )}
    </div>
  );
}
