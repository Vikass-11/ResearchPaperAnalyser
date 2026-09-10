export type PaperStatus = 'queued' | 'processing' | 'completed' | 'failed';

export interface PaperRow {
  id: string;
  original_filename: string;
  storage_path: string;
  status: PaperStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaperAnalysis {
  title: string;
  authors: string[];
  abstract: string;
  keywords: string[];
  simpleSummary: string;
  technicalSummary: string;
  problemStatement: string;
  researchObjective: string;
  methodology: string;
  dataset: string;
  algorithms: string;
  results: string;
  limitations: string;
  conclusion: string;
}

export interface PaperSection {
  name: string;
  content: string;
  orderIndex: number;
}

export interface PaperReference {
  citationKey: string;
  title: string;
  authors: string[];
  year: string;
  rawText: string;
  relationship: string;
  importance: number;
}
