import { Link, useLocation } from 'react-router-dom';
import { BookOpen, LayoutDashboard, FileText, UploadCloud, Settings, FolderClosed } from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Papers', href: '/papers', icon: FileText },
  { name: 'Upload Paper', href: '/upload', icon: UploadCloud },
];

const secondaryNavigation = [
  { name: 'Workspace', href: '#', icon: FolderClosed },
  { name: 'Settings', href: '#', icon: Settings },
];

export function Sidebar() {
  const location = useLocation();

  const isCurrent = (href) => {
    if (href === '/' && location.pathname !== '/') return false;
    if (href !== '/' && location.pathname.startsWith(href)) return true;
    return false;
  };

  return (
    <div className="hidden lg:flex lg:flex-shrink-0">
      <div className="flex flex-col w-64 border-r border-slate-200 bg-white/50 backdrop-blur-xl">
        <div className="flex items-center h-16 px-6 border-b border-slate-200/60">
          <Link to="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
            <img src="/logo.png" alt="Logo" className="w-8 h-8 object-contain rounded-lg shadow-sm" />
            <span className="text-lg font-bold text-slate-800 tracking-tight">ResearchPaper<span className="text-brand-600">Lens</span></span>
          </Link>
        </div>
        
        <div className="flex flex-col flex-1 overflow-y-auto">
          <nav className="flex-1 px-3 py-6 space-y-8">
            <div>
              <h3 className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Research</h3>
              <div className="space-y-1">
                {navigation.map((item) => {
                  const current = isCurrent(item.href);
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                        current 
                          ? 'bg-brand-50 text-brand-700' 
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      }`}
                    >
                      <item.icon
                        className={`mr-3 flex-shrink-0 h-5 w-5 ${
                          current ? 'text-brand-600' : 'text-slate-400 group-hover:text-slate-500'
                        }`}
                        aria-hidden="true"
                      />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>

            <div>
              <h3 className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">System</h3>
              <div className="space-y-1">
                {secondaryNavigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className="group flex items-center px-3 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors"
                  >
                    <item.icon
                      className="mr-3 flex-shrink-0 h-5 w-5 text-slate-400 group-hover:text-slate-500"
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                ))}
              </div>
            </div>
          </nav>
        </div>
      </div>
    </div>
  );
}
