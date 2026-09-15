import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import UploadPaper from './components/UploadPaper'
import PaperList from './components/PaperList'
import PaperDetail from './pages/PaperDetail'

function Dashboard() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey(old => old + 1);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
      <div className="md:col-span-1">
        <UploadPaper onUploadSuccess={handleUploadSuccess} />
      </div>
      <div className="md:col-span-2 flex flex-col gap-6">
        <div>
          <h2 className="text-xl font-semibold mb-4 text-slate-800">My Papers</h2>
          <PaperList refreshTrigger={refreshKey} />
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-slate-50 font-sans">
        <header className="bg-white shadow-sm border-b border-slate-200">
          <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <Link to="/" className="text-2xl font-bold text-slate-900 hover:text-blue-600 transition-colors">
              ScholarGraph AI
            </Link>
          </div>
        </header>
        
        <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
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
