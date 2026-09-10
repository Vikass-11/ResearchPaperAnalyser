const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:4000';

export interface PaperListItem {
  id: string;
  originalFilename: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export async function uploadPaper(file: File) {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(`${API_URL}/papers`, {
    method: 'POST',
    body: form,
  });
  return readJson(response);
}

export async function listPapers(): Promise<PaperListItem[]> {
  const response = await fetch(`${API_URL}/papers`, { cache: 'no-store' });
  return readJson(response);
}

export async function getPaper(id: string) {
  const response = await fetch(`${API_URL}/papers/${id}`, { cache: 'no-store' });
  return readJson(response);
}

export async function getGraph(id: string) {
  const response = await fetch(`${API_URL}/papers/${id}/graph`, { cache: 'no-store' });
  return readJson(response);
}

export async function askQuestion(id: string, question: string) {
  const response = await fetch(`${API_URL}/papers/${id}/questions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  return readJson(response);
}

async function readJson(response: Response) {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  return response.json();
}
