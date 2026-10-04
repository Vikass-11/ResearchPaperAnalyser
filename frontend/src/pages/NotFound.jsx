import { Link } from 'react-router-dom';
import { PageContainer } from '../components/layout/PageContainer';
import { Button } from '../components/common/Button';
import { Home } from 'lucide-react';

export function NotFound() {
  return (
    <PageContainer>
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h1 className="text-9xl font-bold text-slate-200">404</h1>
        <h2 className="text-2xl font-semibold text-slate-800 mt-4 mb-2">Page Not Found</h2>
        <p className="text-slate-500 mb-8 max-w-md">
          The page you are looking for doesn't exist or has been moved.
        </p>
        <Link to="/">
          <Button icon={Home}>Back to Dashboard</Button>
        </Link>
      </div>
    </PageContainer>
  );
}
