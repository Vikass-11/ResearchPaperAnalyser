import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { Papers } from './pages/Papers';
import { UploadPaper } from './pages/UploadPaper';
import { ResearchWorkspace } from './pages/ResearchWorkspace';
import { NotFound } from './pages/NotFound';

// Workspace sub-pages
import { PaperOverview } from './components/research/Overview/PaperOverview';
import { ResearchProfile } from './components/research/Overview/ResearchProfile';
import { RelatedPapers } from './components/research/Related/RelatedPapers';
import { LiteratureAnalysis } from './components/research/Analysis/LiteratureAnalysis';
import { LiteratureSurvey } from './components/research/Survey/LiteratureSurvey';
import { ResearchGaps } from './components/research/Gaps/ResearchGaps';
import { RecentResearch } from './components/research/Recent/RecentResearch';
import { ResearchGraph } from './components/research/Graph/ResearchGraph';
import { PaperComparison } from './components/research/Comparison/PaperComparison';
import { ResearchIntelligence } from './components/research/Intelligence/ResearchIntelligence';
import { ToastProvider } from './components/common/ToastContext';

function LegacyRedirect() {
  const { id } = useParams();
  return <Navigate to={`/papers/${id}/research`} replace />;
}

function App() {
  return (
    <ToastProvider>
      <Router>
        <Routes>
          <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/papers" element={<Papers />} />
          <Route path="/upload" element={<UploadPaper />} />
          
          {/* Legacy redirect */}
          <Route path="/paper/:id" element={<LegacyRedirect />} />
          
          {/* Workspace Routes */}
          <Route path="/papers/:id/research" element={<ResearchWorkspace />}>
            <Route path="overview" element={<PaperOverview />} />
            <Route path="profile" element={<ResearchProfile />} />
            <Route path="related" element={<RelatedPapers />} />
            <Route path="analysis" element={<LiteratureAnalysis />} />
            <Route path="survey" element={<LiteratureSurvey />} />
            <Route path="gaps" element={<ResearchGaps />} />
            <Route path="recent" element={<RecentResearch />} />
            <Route path="graph" element={<ResearchGraph />} />
            <Route path="compare" element={<PaperComparison />} />
            <Route path="intelligence" element={<ResearchIntelligence />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Router>
    </ToastProvider>
  );
}

export default App;
