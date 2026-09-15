import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

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

  if (loading && papers.length === 0) return <p className="text-slate-500">Loading papers...</p>;
  if (papers.length === 0) return <p className="text-slate-500 italic">No papers uploaded yet.</p>;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Title</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Date</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-slate-200">
          {papers.map((paper) => (
            <tr key={paper.id} onClick={() => navigate(`/paper/${paper.id}`)} className="hover:bg-slate-50 cursor-pointer transition-colors">
              <td className="px-6 py-4 text-sm font-medium text-slate-900">
                {paper.title}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                  ${paper.processing_status === 'COMPLETED' ? 'bg-green-100 text-green-800' : 
                    paper.processing_status === 'ERROR' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800 animate-pulse'}`}>
                  {paper.processing_status}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                {new Date(paper.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
