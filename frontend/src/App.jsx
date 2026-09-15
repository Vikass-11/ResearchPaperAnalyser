import { useState } from 'react'
import UploadPaper from './components/UploadPaper'
import PaperList from './components/PaperList'

function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleUploadSuccess = () => {
    setRefreshKey(old => old + 1);
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-slate-900">ScholarGraph AI</h1>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Sidebar / Upload */}
          <div className="md:col-span-1">
            <UploadPaper onUploadSuccess={handleUploadSuccess} />
          </div>

          {/* Main Content / Dashboard */}
          <div className="md:col-span-2 flex flex-col gap-6">
            <div>
              <h2 className="text-xl font-semibold mb-4 text-slate-800">My Papers</h2>
              <PaperList refreshTrigger={refreshKey} />
            </div>
          </div>
          
        </div>
      </main>
    </div>
  )
}

export default App
