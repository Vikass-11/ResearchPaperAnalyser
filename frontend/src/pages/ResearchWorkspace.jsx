import { useEffect, useState } from "react";
import { useParams, Outlet, useNavigate, useLocation } from "react-router-dom";
import { PageContainer } from "../components/layout/PageContainer";
import { ResearchHeader } from "../components/research/ResearchHeader";
import { ResearchTabs } from "../components/research/ResearchTabs";
import { papersApi } from "../api";
import { LoadingState } from "../components/common/LoadingState";
import { ErrorState } from "../components/common/ErrorState";

export function ResearchWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [paper, setPaper] = useState(null);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPaper = async () => {
    try {
      const data = await papersApi.getPaper(id);
      setPaper(data);
      setError(null);
    } catch (err) {
      setError(err.message || "Failed to load paper");
    } finally {
      setLoading(false);
    }
  };

  const fetchPipeline = async () => {
    try {
      const status = await papersApi.getPipelineStatus(id);
      setPipelineStatus(status);
    } catch (err) {
      // Non-fatal if we can't get pipeline status
      console.warn("Failed to fetch pipeline status", err);
    }
  };

  useEffect(() => {
    fetchPaper();
    fetchPipeline();

    const interval = setInterval(() => {
      fetchPipeline();
    }, 5000);

    return () => clearInterval(interval);
  }, [id]);

  // Handle default redirect if at the root /research
  useEffect(() => {
    if (paper && location.pathname === `/papers/${id}/research`) {
      navigate(`/papers/${id}/research/overview`, { replace: true });
    }
  }, [paper, location.pathname, id, navigate]);

  if (loading) return <PageContainer><LoadingState message="Loading research workspace..." /></PageContainer>;
  if (error) return <PageContainer><ErrorState title="Failed to Load Workspace" message={error} onRetry={fetchPaper} /></PageContainer>;
  if (!paper) return <PageContainer><ErrorState title="Paper Not Found" message="The requested paper does not exist." /></PageContainer>;

  return (
    <PageContainer>
      <div className="flex flex-col gap-6">
        <ResearchHeader paper={paper} />
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <ResearchTabs paperId={id} currentPath={location.pathname} />
          <div className="p-6 bg-slate-50/30 min-h-[500px]">
            <Outlet context={{ paper, pipelineStatus }} />
          </div>
        </div>
      </div>
    </PageContainer>
  );
}
