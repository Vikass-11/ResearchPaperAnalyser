import { client } from './client';

export const literatureApi = {
  getResearchProfile: async (paperId) => {
    return client.get(`/papers/${paperId}/literature/research-profile`);
  },
  
  getRelatedPapers: async (paperId, page = 1, limit = 10) => {
    return client.get(`/papers/${paperId}/literature/related?page=${page}&limit=${limit}`);
  },

  discoverRelatedPapers: async (paperId) => {
    return client.post(`/papers/${paperId}/literature/related/discover`, {});
  },

  getRankedPapers: async (paperId, page = 1, limit = 10) => {
    return client.get(`/papers/${paperId}/literature/ranked?page=${page}&limit=${limit}`);
  },

  rankRelatedPapers: async (paperId) => {
    return client.post(`/papers/${paperId}/literature/rank`, {});
  },

  getLiteratureAnalysis: async (paperId) => {
    return client.get(`/papers/${paperId}/literature/analysis`);
  },

  analyzeLiterature: async (paperId) => {
    return client.post(`/papers/${paperId}/literature/analyze`, {});
  },

  getLiteratureSurvey: async (paperId) => {
    return client.get(`/papers/${paperId}/literature/survey`);
  },

  generateLiteratureSurvey: async (paperId) => {
    return client.post(`/papers/${paperId}/literature/survey/generate`, {});
  },

  getResearchGaps: async (paperId) => {
    return client.get(`/papers/${paperId}/literature/gaps`);
  },

  detectResearchGaps: async (paperId) => {
    return client.post(`/papers/${paperId}/literature/gaps/detect`, {});
  },

  getRecentResearch: async (paperId, page = 1, limit = 10) => {
    return client.get(`/papers/${paperId}/literature/recent?page=${page}&limit=${limit}`);
  },

  discoverRecentResearch: async (paperId) => {
    return client.post(`/papers/${paperId}/literature/recent/discover`, {});
  }
};
