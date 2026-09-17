import { useState, useRef } from "react";
import { UploadCloud, FileText, Loader2, AlertCircle } from "lucide-react";

export default function UploadPaper({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/api/v1/papers/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to upload paper");
      }

      await response.json();
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fileInputRef = useRef(null);

  return (
    <div className="glass-card p-6 md:p-8 rounded-2xl">
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-brand-100 p-2 rounded-xl text-brand-600">
          <UploadCloud className="w-5 h-5" />
        </div>
        <h2 className="text-xl font-bold text-slate-800 tracking-tight">Upload Paper</h2>
      </div>
      
      <form onSubmit={handleUpload} className="flex flex-col gap-5">
        <div 
          className={`relative border-2 border-dashed rounded-xl p-8 transition-all text-center
            ${file ? 'border-brand-500 bg-brand-50/50' : 'border-slate-300 hover:border-brand-400 hover:bg-slate-50/50'}
          `}
        >
          <input
            id="file-upload"
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
            {file ? (
              <>
                <FileText className="w-10 h-10 text-brand-500" />
                <div>
                  <p className="text-sm font-semibold text-brand-700">{file.name}</p>
                  <p className="text-xs text-brand-500/80 mt-1">Ready to upload ({(file.size / 1024 / 1024).toFixed(2)} MB)</p>
                </div>
              </>
            ) : (
              <>
                <div className="w-12 h-12 bg-white shadow-sm rounded-full flex items-center justify-center mb-1">
                  <UploadCloud className="w-6 h-6 text-slate-400" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium text-slate-700">
                    <span className="text-brand-600">Click to upload</span> or drag and drop
                  </p>
                  <p className="text-xs text-slate-500">PDF documents only</p>
                </div>
              </>
            )}
          </div>
        </div>
        
        {error && (
          <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg text-sm border border-red-100">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <p>{error}</p>
          </div>
        )}
        
        <button
          type="submit"
          disabled={!file || loading}
          className="relative overflow-hidden w-full bg-brand-600 text-white py-3 px-4 rounded-xl font-semibold 
            hover:bg-brand-700 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed 
            transition-all duration-300 shadow-sm hover:shadow active:scale-[0.98]"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin" /> Analyzing...
            </span>
          ) : (
            "Upload & Analyze"
          )}
        </button>
      </form>
    </div>
  );
}
