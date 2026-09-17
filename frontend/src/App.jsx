import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import UploadPaper from './components/UploadPaper'
import PaperList from './components/PaperList'
import PaperDetail from './pages/PaperDetail'
import { BookOpen } from 'lucide-react'

function Dashboard() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey(old => old + 1);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div className="lg:col-span-1 animate-fade-in">
        <UploadPaper onUploadSuccess={handleUploadSuccess} />
      </div>
      <div className="lg:col-span-2 flex flex-col gap-6 animate-slide-up" style={{ animationDelay: '0.1s', animationFillMode: 'both' }}>
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-slate-800 tracking-tight">My Library</h2>
          </div>
          <PaperList refreshTrigger={refreshKey} />
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen font-sans text-slate-900 selection:bg-brand-100 selection:text-brand-900 relative">
        {/* Premium background */}
        <div className="fixed inset-0 bg-slate-50 -z-20" />
        <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-brand-50/40 via-transparent to-transparent -z-10 pointer-events-none" />
        
        {/* Floating Glass Header */}
        <header className="sticky top-0 z-50 glass-panel border-b border-white/40">
          <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
            <Link to="/" className="text-2xl font-extrabold tracking-tight hover:opacity-80 transition-opacity flex items-center gap-2.5">
              <div className="bg-brand-600 text-white p-2 rounded-xl shadow-md shadow-brand-500/20">
                <BookOpen className="w-5 h-5" />
              </div>
              <span className="text-gradient">ScholarGraph</span>
              <span className="text-slate-900 font-medium text-xl -ml-1">AI</span>
            </Link>
          </div>
        </header>
        
        <main className="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/paper/:id" element={<PaperDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
