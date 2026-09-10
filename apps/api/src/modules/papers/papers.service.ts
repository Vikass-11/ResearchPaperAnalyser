import { Injectable, NotFoundException } from '@nestjs/common';
import type { Express } from 'express';
import { randomUUID } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { DatabaseService } from '../database/database.service';
import { PAPER_QUEUE, QueueService } from '../queue/queue.service';
import { askOllama } from '../../services/ollama';
import type { PaperAnalysis, PaperReference, PaperRow, PaperSection } from './papers.types';

@Injectable()
export class PapersService {
  constructor(
    private readonly db: DatabaseService,
    private readonly queueService: QueueService,
  ) {}

  async createPaper(file: Express.Multer.File) {
    const id = randomUUID();
    const pdfData = await readFile(file.path);
    await this.db.query(
      `INSERT INTO papers (id, original_filename, storage_path, status)
       VALUES ($1, $2, $3, 'queued')`,
      [id, file.originalname, file.path],
    );
    await this.db.query(
      `INSERT INTO paper_files (paper_id, pdf_data) VALUES ($1, $2)`,
      [id, pdfData],
    );

    await this.queueService.paperQueue.add(PAPER_QUEUE, { paperId: id });

    return { id, status: 'queued', filename: file.originalname };
  }

  async listPapers() {
    const result = await this.db.query<PaperRow>(
      `SELECT * FROM papers ORDER BY created_at DESC LIMIT 50`,
    );
    return result.rows.map(toPaperDto);
  }

  async getPaperOrThrow(id: string) {
    const result = await this.db.query<PaperRow>(`SELECT * FROM papers WHERE id = $1`, [id]);
    const paper = result.rows[0];
    if (!paper) throw new NotFoundException('Paper not found.');
    return paper;
  }

  async getPaperBundle(id: string) {
    const paper = await this.getPaperOrThrow(id);
    const [analysis, sections, references] = await Promise.all([
      this.db.query(`SELECT * FROM paper_analyses WHERE paper_id = $1`, [id]),
      this.db.query(`SELECT name, content, order_index FROM paper_sections WHERE paper_id = $1 ORDER BY order_index`, [id]),
      this.db.query(`SELECT * FROM paper_references WHERE paper_id = $1 ORDER BY importance DESC, id ASC`, [id]),
    ]);

    return {
      paper: toPaperDto(paper),
      analysis: analysis.rows[0] ? toAnalysisDto(analysis.rows[0]) : null,
      sections: sections.rows.map((row) => ({
        name: row.name,
        content: row.content,
        orderIndex: row.order_index,
      })),
      references: references.rows.map(toReferenceDto),
    };
  }

  async saveProcessingResult(
    paperId: string,
    analysis: PaperAnalysis,
    sections: PaperSection[],
    chunks: PaperSection[],
    references: PaperReference[],
  ) {
    await this.db.query(
      `INSERT INTO paper_analyses (
        paper_id, title, authors, abstract, keywords, simple_summary, technical_summary,
        problem_statement, research_objective, methodology, dataset, algorithms,
        results, limitations, conclusion, updated_at
      )
      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,NOW())
      ON CONFLICT (paper_id) DO UPDATE SET
        title = EXCLUDED.title,
        authors = EXCLUDED.authors,
        abstract = EXCLUDED.abstract,
        keywords = EXCLUDED.keywords,
        simple_summary = EXCLUDED.simple_summary,
        technical_summary = EXCLUDED.technical_summary,
        problem_statement = EXCLUDED.problem_statement,
        research_objective = EXCLUDED.research_objective,
        methodology = EXCLUDED.methodology,
        dataset = EXCLUDED.dataset,
        algorithms = EXCLUDED.algorithms,
        results = EXCLUDED.results,
        limitations = EXCLUDED.limitations,
        conclusion = EXCLUDED.conclusion,
        updated_at = NOW()`,
      [
        paperId,
        analysis.title,
        analysis.authors,
        analysis.abstract,
        analysis.keywords,
        analysis.simpleSummary,
        analysis.technicalSummary,
        analysis.problemStatement,
        analysis.researchObjective,
        analysis.methodology,
        analysis.dataset,
        analysis.algorithms,
        analysis.results,
        analysis.limitations,
        analysis.conclusion,
      ],
    );

    await this.db.query(`DELETE FROM paper_sections WHERE paper_id = $1`, [paperId]);
    for (const section of sections) {
      await this.db.query(
        `INSERT INTO paper_sections (paper_id, name, content, order_index) VALUES ($1,$2,$3,$4)`,
        [paperId, section.name, section.content, section.orderIndex],
      );
    }

    await this.db.query(`DELETE FROM paper_chunks WHERE paper_id = $1`, [paperId]);
    for (const chunk of chunks) {
      await this.db.query(
        `INSERT INTO paper_chunks (paper_id, section_name, content, token_estimate) VALUES ($1,$2,$3,$4)`,
        [paperId, chunk.name, chunk.content, Math.ceil(chunk.content.length / 4)],
      );
    }

    await this.db.query(`DELETE FROM paper_references WHERE paper_id = $1`, [paperId]);
    for (const reference of references) {
      await this.db.query(
        `INSERT INTO paper_references
          (paper_id, citation_key, title, authors, year, raw_text, relationship, importance)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8)`,
        [
          paperId,
          reference.citationKey,
          reference.title,
          reference.authors,
          reference.year,
          reference.rawText,
          reference.relationship,
          reference.importance,
        ],
      );
    }

    await this.updateStatus(paperId, 'completed');
  }

  async updateStatus(paperId: string, status: string, errorMessage: string | null = null) {
    await this.db.query(
      `UPDATE papers SET status = $2, error_message = $3, updated_at = NOW() WHERE id = $1`,
      [paperId, status, errorMessage],
    );
  }

  async answerQuestion(paperId: string, question: string) {
    await this.getPaperOrThrow(paperId);
    const chunks = await this.db.query(
      `SELECT id, section_name, content
       FROM paper_chunks
       WHERE paper_id = $1
       ORDER BY id ASC
       LIMIT 80`,
      [paperId],
    );

    const selected = rankChunks(question, chunks.rows).slice(0, 5);
    const context = selected
      .map((chunk, index) => `[Source ${index + 1}: ${chunk.section_name}]\n${chunk.content}`)
      .join('\n\n');

    const ollamaAnswer = await askOllama(
      `Answer the question using only the research paper context. Be concise and cite source labels when helpful.\n\nQuestion: ${question}\n\nContext:\n${context}`,
    );

    const answer =
      ollamaAnswer ??
      `Based on the most relevant paper sections, ${fallbackAnswer(question, selected.map((item) => item.content))}`;

    await this.db.query(
      `INSERT INTO qa_history (paper_id, question, answer, sources) VALUES ($1,$2,$3,$4)`,
      [
        paperId,
        question,
        answer,
        JSON.stringify(selected.map((chunk) => ({ id: chunk.id, sectionName: chunk.section_name }))),
      ],
    );

    return {
      answer,
      sources: selected.map((chunk) => ({
        id: chunk.id,
        sectionName: chunk.section_name,
        preview: chunk.content.slice(0, 240),
      })),
    };
  }

  async getGraph(paperId: string) {
    const bundle = await this.getPaperBundle(paperId);
    const title = bundle.analysis?.title || bundle.paper.originalFilename;
    const nodes: any[] = [
      {
        id: paperId,
        type: 'input',
        data: { label: title },
        position: { x: 0, y: 0 },
      },
    ];

    const edges: any[] = [];
    bundle.references.slice(0, 12).forEach((reference, index) => {
      const angle = (Math.PI * 2 * index) / Math.max(bundle.references.length, 1);
      const id = `ref-${reference.id}`;
      nodes.push({
        id,
        data: { label: reference.title || reference.rawText.slice(0, 80) },
        position: {
          x: Math.round(Math.cos(angle) * 360),
          y: Math.round(Math.sin(angle) * 260),
        },
      });
      edges.push({
        id: `${paperId}-${id}`,
        source: paperId,
        target: id,
        label: reference.relationship,
      });
    });

    return { nodes, edges };
  }
}

function toPaperDto(row: PaperRow) {
  return {
    id: row.id,
    originalFilename: row.original_filename,
    status: row.status,
    errorMessage: row.error_message,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  };
}

function toAnalysisDto(row: any) {
  return {
    title: row.title,
    authors: row.authors ?? [],
    abstract: row.abstract,
    keywords: row.keywords ?? [],
    simpleSummary: row.simple_summary,
    technicalSummary: row.technical_summary,
    problemStatement: row.problem_statement,
    researchObjective: row.research_objective,
    methodology: row.methodology,
    dataset: row.dataset,
    algorithms: row.algorithms,
    results: row.results,
    limitations: row.limitations,
    conclusion: row.conclusion,
  };
}

function toReferenceDto(row: any) {
  return {
    id: row.id,
    citationKey: row.citation_key,
    title: row.title,
    authors: row.authors ?? [],
    year: row.year,
    rawText: row.raw_text,
    relationship: row.relationship,
    importance: row.importance,
  };
}

function rankChunks(question: string, chunks: any[]) {
  const terms = new Set(question.toLowerCase().split(/[^a-z0-9]+/).filter((term) => term.length > 2));
  return [...chunks].sort((a, b) => scoreChunk(b, terms) - scoreChunk(a, terms));
}

function scoreChunk(chunk: any, terms: Set<string>) {
  const text = `${chunk.section_name} ${chunk.content}`.toLowerCase();
  let score = 0;
  for (const term of terms) {
    if (text.includes(term)) score += 1;
  }
  return score + Math.min(chunk.content.length / 2000, 1);
}

function fallbackAnswer(question: string, contexts: string[]) {
  const combined = contexts.join(' ').replace(/\s+/g, ' ').trim();
  if (!combined) return 'I could not find enough extracted text to answer this question.';

  const lowerQuestion = question.toLowerCase();
  if (lowerQuestion.includes('limitation')) {
    return firstSentenceWith(combined, ['limitation', 'future work', 'constraint']) ?? combined.slice(0, 600);
  }
  if (lowerQuestion.includes('method')) {
    return firstSentenceWith(combined, ['method', 'approach', 'proposed', 'model']) ?? combined.slice(0, 600);
  }
  if (lowerQuestion.includes('dataset') || lowerQuestion.includes('data')) {
    return firstSentenceWith(combined, ['dataset', 'data', 'benchmark']) ?? combined.slice(0, 600);
  }
  return combined.slice(0, 700);
}

function firstSentenceWith(text: string, terms: string[]) {
  const sentences = text.split(/(?<=[.!?])\s+/);
  return sentences.find((sentence) => terms.some((term) => sentence.toLowerCase().includes(term)));
}
