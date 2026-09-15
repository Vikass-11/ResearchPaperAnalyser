import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, BookOpen, Layers, CheckCircle, FileText, AlertTriangle } from "lucide-react";

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
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/" className="p-2 hover:bg-slate-200 rounded-full transition-colors">
          <ArrowLeft className="w-5 h-5 text-slate-600" />
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
          <div className="lg:col-span-1 flex flex-col gap-2">
            <button 
              onClick={() => setActiveSection("ai_summary")}
              className={`text-left px-4 py-3 rounded-lg flex items-center gap-3 transition-all ${activeSection === "ai_summary" ? "bg-blue-50 text-blue-700 font-medium shadow-sm border border-blue-100" : "hover:bg-slate-100 text-slate-700 border border-transparent"}`}>
              <BookOpen className="w-4 h-4" /> AI Summary & Insights
            </button>
            <button 
              onClick={() => setActiveSection("methodology")}
              className={`text-left px-4 py-3 rounded-lg flex items-center gap-3 transition-all ${activeSection === "methodology" ? "bg-blue-50 text-blue-700 font-medium shadow-sm border border-blue-100" : "hover:bg-slate-100 text-slate-700 border border-transparent"}`}>
              <Layers className="w-4 h-4" /> Methodology & Results
            </button>
            <button 
              onClick={() => setActiveSection("extracted")}
              className={`text-left px-4 py-3 rounded-lg flex items-center gap-3 transition-all ${activeSection === "extracted" ? "bg-blue-50 text-blue-700 font-medium shadow-sm border border-blue-100" : "hover:bg-slate-100 text-slate-700 border border-transparent"}`}>
              <FileText className="w-4 h-4" /> Extracted Sections
            </button>
          </div>

          {/* Content Area */}
          <div className="lg:col-span-3">
            
            {activeSection === "ai_summary" && (
              <div className="flex flex-col gap-6">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                  <h3 className="text-lg font-semibold text-slate-800 mb-3 border-b pb-2">Executive Summary</h3>
                  <p className="text-slate-600 whitespace-pre-wrap leading-relaxed">{paper.summary}</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 className="text-lg font-semibold text-slate-800 mb-3 flex items-center gap-2 border-b pb-2">
                      <CheckCircle className="w-5 h-5 text-green-500" /> Key Contributions
                    </h3>
                    <ul className="list-disc list-inside text-slate-600 space-y-2">
                      {paper.contributions?.map((c, i) => <li key={i}>{c}</li>)}
                    </ul>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h3 className="text-lg font-semibold text-slate-800 mb-3 border-b pb-2">Core Problem</h3>
                    <p className="text-slate-600">{paper.problem_statement}</p>
                  </div>
                </div>
              </div>
            )}

            {activeSection === "methodology" && (
              <div className="flex flex-col gap-6">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                  <h3 className="text-lg font-semibold text-slate-800 mb-3 border-b pb-2">Methodology</h3>
                  <p className="text-slate-600 whitespace-pre-wrap leading-relaxed">{paper.methodology}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                  <h3 className="text-lg font-semibold text-slate-800 mb-3 border-b pb-2">Results & Findings</h3>
                  <ul className="list-disc list-inside text-slate-600 space-y-2">
                    {paper.results?.map((r, i) => <li key={i} className="leading-relaxed">{r}</li>)}
                  </ul>
                </div>
              </div>
            )}

            {activeSection === "extracted" && (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between mb-2">
                   <h3 className="text-lg font-semibold text-slate-800">Raw Extracted Sections</h3>
                   <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded">via GROBID TEI</span>
                </div>
                {paper.sections?.length > 0 ? paper.sections.map(sec => (
                  <div key={sec.id} className="bg-white p-5 rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
                    <h4 className="font-semibold text-slate-900 mb-3 border-b pb-2">{sec.section_name}</h4>
                    <p className="text-sm text-slate-600 whitespace-pre-wrap leading-relaxed line-clamp-3 hover:line-clamp-none transition-all cursor-pointer" title="Click to expand">
                      {sec.content}
                    </p>
                  </div>
                )) : <p className="text-slate-500 italic">No sections could be cleanly extracted.</p>}
              </div>
            )}

          </div>
        </div>
      )}
    </div>
  );
}
