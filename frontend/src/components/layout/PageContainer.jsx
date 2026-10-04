export function PageContainer({ children, title, subtitle, action }) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full animate-fade-in">
      {(title || action) && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4">
          <div>
            {title && <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{title}</h1>}
            {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
          </div>
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      )}
      <div className="animate-slide-up" style={{ animationDelay: '0.1s', animationFillMode: 'both' }}>
        {children}
      </div>
    </div>
  );
}
