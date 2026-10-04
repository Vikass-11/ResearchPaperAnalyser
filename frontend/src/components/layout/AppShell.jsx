import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { Outlet } from 'react-router-dom';

export function AppShell() {
  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans text-slate-900 selection:bg-brand-100 selection:text-brand-900 relative">
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-brand-50/40 via-transparent to-transparent pointer-events-none print:hidden" />
      <div className="print:hidden h-full flex flex-shrink-0">
        <Sidebar />
      </div>
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden relative z-10 print:overflow-visible">
        <div className="print:hidden">
          <Topbar />
        </div>
        <main className="flex-1 overflow-y-auto print:overflow-visible">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
