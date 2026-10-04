import { API_BASE_URL, ApiError } from './client';

const downloadBlob = async (url, fallbackFilename) => {
  const response = await fetch(url);
  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      throw new ApiError('Failed to export document', 'EXPORT_FAILED', response.status);
    }
    const message = errorData?.error?.message || 'Export failed';
    throw new ApiError(message, errorData?.error?.code, response.status);
  }

  const blob = await response.blob();
  
  // Extract filename from Content-Disposition if available
  let filename = fallbackFilename;
  const disposition = response.headers.get('Content-Disposition');
  if (disposition && disposition.indexOf('attachment') !== -1) {
    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
    const matches = filenameRegex.exec(disposition);
    if (matches != null && matches[1]) { 
      filename = matches[1].replace(/['"]/g, '');
    }
  }

  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
};

export const exportsApi = {
  downloadJson: async (paperId, title = 'research') => {
    const url = `${API_BASE_URL}/papers/${paperId}/export/json`;
    await downloadBlob(url, `scholargraph-${title.replace(/[^a-z0-9]/gi, '-').toLowerCase()}.json`);
  },
  
  downloadMarkdown: async (paperId, title = 'research') => {
    const url = `${API_BASE_URL}/papers/${paperId}/export/markdown`;
    await downloadBlob(url, `scholargraph-${title.replace(/[^a-z0-9]/gi, '-').toLowerCase()}.md`);
  },

  downloadPdf: async (paperId, title = 'research') => {
    const url = `${API_BASE_URL}/papers/${paperId}/export/pdf`;
    await downloadBlob(url, `scholargraph-${title.replace(/[^a-z0-9]/gi, '-').toLowerCase()}.pdf`);
  },
};
