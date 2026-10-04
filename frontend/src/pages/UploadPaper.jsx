import { PageContainer } from '../components/layout/PageContainer';
import UploadPaperComponent from '../components/UploadPaper';
import { useNavigate } from 'react-router-dom';

export function UploadPaper() {
  const navigate = useNavigate();

  const handleUploadSuccess = () => {
    // Navigate to papers list after upload
    navigate('/papers');
  };

  return (
    <PageContainer 
      title="Upload Research Paper" 
      subtitle="Upload a PDF file to begin the analysis workflow."
    >
      <div className="max-w-2xl">
        <UploadPaperComponent onUploadSuccess={handleUploadSuccess} />
      </div>
    </PageContainer>
  );
}
