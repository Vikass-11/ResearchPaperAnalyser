import { Menu, Search, UserCircle } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function Topbar() {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/papers?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };
  return (
    <header className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-200/60 h-16 flex-shrink-0">
      <div className="flex-1 px-4 flex justify-between h-full lg:px-8">
        <div className="flex-1 flex items-center lg:hidden">
          <button className="p-2 -ml-2 text-slate-500 hover:text-slate-600 rounded-md">
            <span className="sr-only">Open sidebar</span>
            <Menu className="h-6 w-6" aria-hidden="true" />
          </button>
        </div>
        
        <div className="flex-1 flex justify-between">
          <div className="flex-1 flex items-center">
            {/* Search Placeholder */}
            <div className="w-full max-w-lg hidden sm:block">
              <form onSubmit={handleSearch}>
                <label htmlFor="search" className="sr-only">Search papers</label>
                <div className="relative text-slate-400 focus-within:text-slate-600">
                  <div className="pointer-events-none absolute inset-y-0 left-0 pl-3 flex items-center">
                    <Search className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <input
                    id="search"
                    className="block w-full bg-slate-100/50 py-2 pl-10 pr-3 border border-transparent rounded-lg leading-5 text-slate-900 placeholder-slate-500 focus:outline-none focus:bg-white focus:ring-1 focus:ring-brand-500 focus:border-brand-500 sm:text-sm transition-all"
                    placeholder="Search papers by title..."
                    type="search"
                    name="search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </form>
            </div>
          </div>
          
          <div className="ml-4 flex items-center gap-4">
            <button className="bg-white rounded-full flex text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500">
              <span className="sr-only">Open user menu</span>
              <UserCircle className="h-8 w-8 text-slate-400" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
