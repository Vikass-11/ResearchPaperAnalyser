import { client } from './client';

export const papersApi = {
  getPapers: async (page = 1, limit = 20) => {
    return client.get(`/papers/?page=${page}&limit=${limit}`);
  },
  
  getPaper: async (paperId) => {
    return client.get(`/papers/${paperId}`);
  },
  
  uploadPaper: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/papers/upload', formData);
  },
  
  deletePaper: async (paperId) => {
    return client.delete(`/papers/${paperId}`);
  },

  getPipelineStatus: async (paperId) => {
    return client.get(`/papers/${paperId}/pipeline/status`);
  },

  getResearchSummary: async (paperId) => {
    return client.get(`/papers/${paperId}/research-summary`);
  },
};
