import { PageContainer } from '../components/layout/PageContainer';
import PaperList from '../components/PaperList';
import { Link } from 'react-router-dom';
import { Button } from '../components/common/Button';
import { UploadCloud } from 'lucide-react';

export function Papers() {
  return (
    <PageContainer 
      title="Research Papers" 
      subtitle="Manage your uploaded research papers and analyses."
      action={
        <Link to="/upload">
          <Button icon={UploadCloud}>Upload Paper</Button>
        </Link>
      }
    >
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6">
          <PaperList />
        </div>
      </div>
    </PageContainer>
  );
}
