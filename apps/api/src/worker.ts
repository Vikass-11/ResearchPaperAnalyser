import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { Worker } from 'bullmq';
import IORedis from 'ioredis';
import pdf from 'pdf-parse';
import { AppModule } from './modules/app.module';
import { DatabaseService } from './modules/database/database.service';
import { PAPER_QUEUE } from './modules/queue/queue.service';
import { PapersService } from './modules/papers/papers.service';
import type { PaperAnalysis, PaperReference, PaperSection } from './modules/papers/papers.types';
import { askOllama } from './services/ollama';
import { extractWithGrobid } from './services/grobid';

async function bootstrapWorker() {
  const app = await NestFactory.createApplicationContext(AppModule);
  const db = app.get(DatabaseService);
  const papersService = app.get(PapersService);
  const connection = new IORedis(process.env.REDIS_URL ?? 'redis://localhost:6379', {
    maxRetriesPerRequest: null,
  });

  const worker = new Worker(
    PAPER_QUEUE,
    async (job) => {
      const paperId = job.data.paperId as string;
      const paper = await db.query(`SELECT * FROM papers WHERE id = $1`, [paperId]);
      const row = paper.rows[0];
      if (!row) throw new Error(`Paper ${paperId} not found.`);

      await papersService.updateStatus(paperId, 'processing');
      try {
        let sections: PaperSection[];
        let references: PaperReference[];
        let title: string | undefined;
        let authors: string[] | undefined;
        let abstract: string | undefined;
        let fullText: string;

        try {
          const file = await db.query(`SELECT pdf_data FROM paper_files WHERE paper_id = $1`, [paperId]);
          const buffer = file.rows[0]?.pdf_data;
          if (!buffer) throw new Error('PDF bytes were not found for this paper.');

          const grobidResult = await extractWithGrobid(buffer);
          sections = grobidResult.sections;
          references = grobidResult.references;
          title = grobidResult.title;
          authors = grobidResult.authors;
          abstract = grobidResult.abstract;
          fullText = grobidResult.fullText;

          references = references.map((ref) => {
            const relationship = classifyReferenceRelationship(ref.citationKey, fullText);
            return {
              ...ref,
              relationship,
              importance: scoreReferenceImportance(ref.citationKey, fullText, relationship),
            };
          });
        } catch (grobidError) {
          console.warn('GROBID extraction failed, falling back to heuristic extraction:', grobidError);
          fullText = await extractPdfText(db, paperId, row.storage_path);
          sections = detectSections(fullText);
          references = extractReferences(sections, fullText);
        }

        if (abstract && !sections.some((s) => s.name.toLowerCase() === 'abstract')) {
          sections.unshift({ name: 'Abstract', content: abstract, orderIndex: 0 });
          sections = sections.map((s, i) => ({ ...s, orderIndex: i }));
        }

        const chunks = chunkSections(sections);
        const analysis = await analyzePaper(row.original_filename, sections, references, title, authors);
        await papersService.saveProcessingResult(paperId, analysis, sections, chunks, references);
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unknown processing error';
        await papersService.updateStatus(paperId, 'failed', message);
        throw error;
      }
    },
    { connection, concurrency: Number(process.env.WORKER_CONCURRENCY ?? 2) },
  );

  worker.on('completed', (job) => console.log(`Processed paper job ${job.id}`));
  worker.on('failed', (job, error) => console.error(`Paper job ${job?.id} failed`, error));

  const shutdown = async () => {
    await worker.close();
    await connection.quit();
    await app.close();
    process.exit(0);
  };

  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
  console.log('ScholarGraph paper worker running');
}

async function extractPdfText(db: DatabaseService, paperId: string, _path: string) {
  const file = await db.query(`SELECT pdf_data FROM paper_files WHERE paper_id = $1`, [paperId]);
  const buffer = file.rows[0]?.pdf_data;
  if (!buffer) throw new Error('PDF bytes were not found for this paper.');
  const result = await pdf(buffer);
  return normalizeText(result.text);
}

function detectSections(text: string): PaperSection[] {
  const headings = [
    'abstract',
    'keywords',
    'introduction',
    'related work',
    'literature review',
    'methodology',
    'methods',
    'proposed method',
    'experiments',
    'experimental setup',
    'results',
    'discussion',
    'limitations',
    'conclusion',
    'references',
  ];

  const lines = text.split('\n').map((line) => line.trim()).filter(Boolean);
  const sections: PaperSection[] = [];
  let currentName = 'front matter';
  let currentLines: string[] = [];

  const flush = () => {
    const content = currentLines.join('\n').trim();
    if (content) {
      sections.push({ name: titleCase(currentName), content, orderIndex: sections.length });
    }
    currentLines = [];
  };

  for (const line of lines) {
    const clean = line
      .replace(/^\d+(\.\d+)*\s+/, '')
      .replace(/^[IVX]+\.\s+/i, '')
      .trim()
      .toLowerCase();

    const isHeading = headings.includes(clean) || headings.some((heading) => clean === heading.toLowerCase());
    if (isHeading) {
      flush();
      currentName = clean;
      continue;
    }
    currentLines.push(line);
  }
  flush();

  if (!sections.some((section) => section.name.toLowerCase() === 'abstract')) {
    const abstract = extractBetween(text, /abstract/i, /(keywords|introduction|1\s+introduction)/i);
    if (abstract) sections.unshift({ name: 'Abstract', content: abstract, orderIndex: 0 });
  }

  return sections.map((section, index) => ({ ...section, orderIndex: index })).slice(0, 40);
}

function extractReferences(sections: PaperSection[], fullText: string): PaperReference[] {
  const referenceText =
    sections.find((section) => section.name.toLowerCase() === 'references')?.content ??
    extractBetween(fullText, /references/i, /appendix|acknowledg/i) ??
    '';

  const rawReferences = splitReferences(referenceText);
  return rawReferences.slice(0, 40).map((raw, index) => {
    const citationKey = raw.match(/^\s*\[?(\d+)\]?/)?.[1] ?? String(index + 1);
    const title = guessReferenceTitle(raw);
    const year = raw.match(/\b(19|20)\d{2}\b/)?.[0] ?? '';
    const relationship = classifyReferenceRelationship(citationKey, fullText);
    return {
      citationKey,
      title,
      authors: guessAuthors(raw),
      year,
      rawText: raw,
      relationship,
      importance: scoreReferenceImportance(citationKey, fullText, relationship),
    };
  });
}

function splitReferences(referenceText: string) {
  const text = referenceText.replace(/\s+/g, ' ').trim();
  if (!text) return [];

  const numbered = text
    .split(/(?=\s*\[?\d{1,3}\]?\s+[A-Z])/g)
    .map((item) => item.trim())
    .filter((item) => item.length > 30);

  if (numbered.length > 1) return numbered;

  return text
    .split(/(?<=\.\s)(?=[A-Z][A-Za-z'-]+,\s+[A-Z]\.)/g)
    .map((item) => item.trim())
    .filter((item) => item.length > 30);
}

async function analyzePaper(
  filename: string,
  sections: PaperSection[],
  references: PaperReference[],
  preExtractedTitle?: string,
  preExtractedAuthors?: string[],
): Promise<PaperAnalysis> {
  const frontMatter = sectionContent(sections, 'front matter');
  const abstract = sectionContent(sections, 'abstract') || firstParagraph(frontMatter);
  const introduction = sectionContent(sections, 'introduction');
  const methodology =
    sectionContent(sections, 'methodology') ||
    sectionContent(sections, 'methods') ||
    sectionContent(sections, 'proposed method');
  const results = sectionContent(sections, 'results') || sectionContent(sections, 'discussion');
  const conclusion = sectionContent(sections, 'conclusion');
  const limitations = sectionContent(sections, 'limitations') || findSentences(fullPaperText(sections), ['limitation', 'future work']);

  const ollamaSummary = await askOllama(
    `Create a concise research-paper analysis from these extracted sections. Return normal text, not JSON.\n\nAbstract:\n${abstract}\n\nMethodology:\n${methodology}\n\nResults:\n${results}\n\nConclusion:\n${conclusion}`,
  );

  return {
    title: preExtractedTitle || guessTitle(frontMatter, filename),
    authors: preExtractedAuthors?.length ? preExtractedAuthors : guessPaperAuthors(frontMatter),
    abstract,
    keywords: guessKeywords(sectionContent(sections, 'keywords'), abstract),
    simpleSummary:
      ollamaSummary ??
      summarizeSimple(abstract || introduction || fullPaperText(sections).slice(0, 1200)),
    technicalSummary: summarizeTechnical(abstract, methodology, results),
    problemStatement: findSentences(introduction || abstract, ['problem', 'challenge', 'difficult', 'gap']) || firstSentences(introduction || abstract, 2),
    researchObjective: findSentences(abstract || introduction, ['objective', 'aim', 'propose', 'present', 'develop']) || firstSentences(abstract, 2),
    methodology: firstSentences(methodology, 4),
    dataset: findSentences(fullPaperText(sections), ['dataset', 'data set', 'benchmark', 'corpus']),
    algorithms: findSentences(fullPaperText(sections), ['algorithm', 'model', 'transformer', 'cnn', 'lstm', 'bert', 'classifier']),
    results: firstSentences(results, 4),
    limitations: limitations || 'No explicit limitations section was detected in the extracted text.',
    conclusion: firstSentences(conclusion, 4),
  };
}

function chunkSections(sections: PaperSection[]): PaperSection[] {
  const chunks: PaperSection[] = [];
  const maxLength = 1800;

  for (const section of sections) {
    const paragraphs = section.content.split(/\n{2,}|(?<=\.)\s+(?=[A-Z])/g);
    let current = '';
    for (const paragraph of paragraphs) {
      if ((current + paragraph).length > maxLength && current) {
        chunks.push({ name: section.name, content: current.trim(), orderIndex: chunks.length });
        current = '';
      }
      current += `${paragraph.trim()} `;
    }
    if (current.trim()) {
      chunks.push({ name: section.name, content: current.trim(), orderIndex: chunks.length });
    }
  }

  return chunks.slice(0, 250);
}

function normalizeText(text: string) {
  return text
    .replace(/\r/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function sectionContent(sections: PaperSection[], name: string) {
  return sections.find((section) => section.name.toLowerCase() === name.toLowerCase())?.content ?? '';
}

function fullPaperText(sections: PaperSection[]) {
  return sections.map((section) => section.content).join('\n\n');
}

function extractBetween(text: string, start: RegExp, end: RegExp) {
  const startMatch = start.exec(text);
  if (!startMatch || startMatch.index === undefined) return '';
  const tail = text.slice(startMatch.index + startMatch[0].length);
  const endMatch = end.exec(tail);
  return (endMatch ? tail.slice(0, endMatch.index) : tail).trim().slice(0, 5000);
}

function titleCase(value: string) {
  return value.replace(/\w\S*/g, (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase());
}

function firstParagraph(text: string) {
  return text.split(/\n{2,}/).find((paragraph) => paragraph.length > 80) ?? '';
}

function firstSentences(text: string, count: number) {
  return text.split(/(?<=[.!?])\s+/).filter(Boolean).slice(0, count).join(' ').trim();
}

function findSentences(text: string, terms: string[]) {
  const matches = text
    .split(/(?<=[.!?])\s+/)
    .filter((sentence) => terms.some((term) => sentence.toLowerCase().includes(term)))
    .slice(0, 3);
  return matches.join(' ').trim();
}

function summarizeSimple(text: string) {
  const seed = firstSentences(text, 3);
  return seed
    ? `This paper mainly studies: ${seed}`
    : 'The paper text was extracted, but there was not enough clean abstract content to summarize confidently.';
}

function summarizeTechnical(abstract: string, methodology: string, results: string) {
  return [firstSentences(abstract, 2), firstSentences(methodology, 2), firstSentences(results, 2)]
    .filter(Boolean)
    .join(' ');
}

function guessTitle(frontMatter: string, filename: string) {
  const lines = frontMatter.split('\n').map((line) => line.trim()).filter(Boolean);
  const candidate = lines.find((line) => line.length > 12 && line.length < 180 && !line.includes('@'));
  return candidate ?? filename.replace(/\.pdf$/i, '').replace(/[-_]/g, ' ');
}

function guessPaperAuthors(frontMatter: string) {
  const lines = frontMatter.split('\n').map((line) => line.trim()).filter(Boolean);
  const likely = lines.slice(1, 5).find((line) => /,| and |Department|University/i.test(line));
  if (!likely) return [];
  return likely
    .replace(/Department.*$/i, '')
    .split(/,| and /i)
    .map((author) => author.trim())
    .filter((author) => author.length > 2 && author.length < 80)
    .slice(0, 10);
}

function guessKeywords(keywordText: string, abstract: string) {
  const explicit = keywordText
    .replace(/^keywords\s*[-:]/i, '')
    .split(/[,;]/)
    .map((item) => item.trim())
    .filter((item) => item.length > 2 && item.length < 60)
    .slice(0, 10);

  if (explicit.length) return explicit;

  const stop = new Set(['this', 'that', 'with', 'from', 'paper', 'using', 'used', 'based', 'their', 'which', 'were']);
  const words = abstract.toLowerCase().match(/[a-z][a-z-]{4,}/g) ?? [];
  const counts = new Map<string, number>();
  for (const word of words) {
    if (!stop.has(word)) counts.set(word, (counts.get(word) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([word]) => word);
}

function guessReferenceTitle(raw: string) {
  const quoted = raw.match(/["“](.*?)["”]/)?.[1];
  if (quoted && quoted.length > 5) return quoted;

  const parts = raw.split('.');
  const candidate = parts.find((part) => part.trim().split(/\s+/).length >= 4 && !/\b(19|20)\d{2}\b/.test(part));
  return candidate?.replace(/^\s*\[?\d+\]?\s*/, '').trim().slice(0, 180) ?? '';
}

function guessAuthors(raw: string) {
  const beforeTitle = raw.split(/["“]/)[0] ?? raw.split('.')[0] ?? '';
  return beforeTitle
    .replace(/^\s*\[?\d+\]?\s*/, '')
    .split(/,| and /i)
    .map((item) => item.trim())
    .filter((item) => item.length > 2 && item.length < 80)
    .slice(0, 8);
}

function classifyReferenceRelationship(citationKey: string, fullText: string) {
  const contexts = citationContexts(citationKey, fullText).join(' ').toLowerCase();
  if (/dataset|benchmark|corpus|data set/.test(contexts)) return 'uses dataset from';
  if (/method|model|architecture|algorithm|framework|approach/.test(contexts)) return 'uses method from';
  if (/compare|baseline|outperform|versus|against/.test(contexts)) return 'compares with';
  if (/survey|review|previous|related work|prior/.test(contexts)) return 'background work';
  if (/extend|build upon|based on/.test(contexts)) return 'builds upon';
  return 'referenced work';
}

function scoreReferenceImportance(citationKey: string, fullText: string, relationship: string) {
  const mentions = citationContexts(citationKey, fullText).length;
  const relationshipBonus = relationship === 'uses method from' || relationship === 'uses dataset from' ? 3 : 1;
  return Math.max(1, Math.min(10, mentions + relationshipBonus));
}

function citationContexts(citationKey: string, fullText: string) {
  const contexts: string[] = [];
  const escaped = citationKey.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`\\[${escaped}\\]|\\(${escaped}\\)`, 'g');
  let match: RegExpExecArray | null;
  while ((match = regex.exec(fullText)) && contexts.length < 20) {
    const start = Math.max(0, match.index - 160);
    const end = Math.min(fullText.length, match.index + 180);
    contexts.push(fullText.slice(start, end));
  }
  return contexts;
}

bootstrapWorker().catch((error) => {
  console.error(error);
  process.exit(1);
});
