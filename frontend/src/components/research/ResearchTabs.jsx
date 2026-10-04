import { Link } from "react-router-dom";

export function ResearchTabs({ paperId, currentPath }) {
  const tabs = [
    { name: 'Overview', path: `/papers/${paperId}/research/overview` },
    { name: 'Research Profile', path: `/papers/${paperId}/research/profile` },
    { name: 'Related Papers', path: `/papers/${paperId}/research/related` },
    { name: 'Literature Analysis', path: `/papers/${paperId}/research/analysis` },
    { name: 'Literature Survey', path: `/papers/${paperId}/research/survey` },
    { name: 'Research Gaps', path: `/papers/${paperId}/research/gaps` },
    { name: 'Recent Research', path: `/papers/${paperId}/research/recent` },
    { name: 'Landscape Graph', path: `/papers/${paperId}/research/graph` },
    { name: 'Compare', path: `/papers/${paperId}/research/compare` },
    { name: 'Research Intelligence', path: `/papers/${paperId}/research/intelligence` },
  ];

  return (
    <div className="border-b border-slate-200 bg-white overflow-x-auto custom-scrollbar print:hidden">
      <nav className="flex space-x-1 px-4" aria-label="Research sections">
        {tabs.map((tab) => {
          const isActive = currentPath === tab.path || (tab.path.endsWith('/overview') && currentPath === `/papers/${paperId}/research`);
          
          return (
            <Link
              key={tab.name}
              to={tab.path}
              className={`
                whitespace-nowrap py-4 px-4 border-b-2 font-medium text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 rounded-t-sm
                ${isActive
                  ? 'border-brand-500 text-brand-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                }
              `}
              aria-current={isActive ? 'page' : undefined}
            >
              {tab.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
