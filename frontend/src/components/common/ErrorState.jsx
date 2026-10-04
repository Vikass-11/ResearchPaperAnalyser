import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './Button';

export function ErrorState({ title = 'Something went wrong', message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-slate-800 bg-red-50/50 rounded-2xl border border-red-100 min-h-[200px]">
      <div className="bg-red-100 text-red-600 p-3 rounded-xl mb-4">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {message && <p className="text-slate-600 text-center mb-6 max-w-md">{message}</p>}
      
      {onRetry && (
        <Button variant="outline" onClick={onRetry} icon={RefreshCw}>
          Retry
        </Button>
      )}
    </div>
  );
}
