'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Background, Controls, ReactFlow } from 'reactflow';
import 'reactflow/dist/style.css';
import {
  askQuestion,
  getGraph,
  getPaper,
  listPapers,
  uploadPaper,
  type PaperListItem,
} from '../lib/api';
import { ChangeEvent, FormEvent, useMemo, useState } from 'react';
import {
  Brain,
  CheckCircle2,
  Clock3,
  FileText,
  GitBranch,
  Loader2,
  MessageSquareText,
  Upload,
  XCircle,
} from 'lucide-react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

export default function Page() {
  return (
    <QueryClientProvider client={queryClient}>
      <ScholarGraphApp />
    </QueryClientProvider>
  );
}

function ScholarGraphApp() {
  const client = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const papersQuery = useQuery({
    queryKey: ['papers'],
    queryFn: listPapers,
    refetchInterval: 4000,
  });

  const selectedPaper = selectedId ?? papersQuery.data?.[0]?.id ?? null;

  const uploadMutation = useMutation({
    mutationFn: uploadPaper,
    onSuccess: (data) => {
      setSelectedId(data.id);
      client.invalidateQueries({ queryKey: ['papers'] });
    },
  });

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-ink/10 bg-paper">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal text-ink">ScholarGraph AI</h1>
            <p className="mt-1 text-sm text-moss">Research paper analyzer with local-first citation intelligence.</p>
          </div>
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-md bg-ink px-4 py-2 text-sm font-medium text-white shadow-soft">
            {uploadMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            Upload PDF
            <input type="file" accept="application/pdf" className="sr-only" onChange={onFileChange} />
          </label>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-5 px-5 py-5 lg:grid-cols-[320px_1fr]">
        <aside className="rounded-lg border border-ink/10 bg-white/70 p-3 shadow-soft">
          <div className="mb-3 flex items-center gap-2 px-1 text-sm font-semibold text-graphite">
            <FileText className="h-4 w-4" />
            Papers
          </div>
          <div className="space-y-2">
            {papersQuery.data?.length ? (
              papersQuery.data.map((paper) => (
                <PaperButton
                  key={paper.id}
                  paper={paper}
                  active={paper.id === selectedPaper}
                  onClick={() => setSelectedId(paper.id)}
                />
              ))
            ) : (
              <div className="rounded-md border border-dashed border-moss/40 bg-paper p-4 text-sm text-moss">
                Upload an IEEE or research PDF to start the analysis pipeline.
              </div>
            )}
          </div>
        </aside>

        {selectedPaper ? <PaperWorkspace paperId={selectedPaper} /> : <EmptyWorkspace />}
      </div>
    </main>
  );
}

function PaperButton({
  paper,
  active,
  onClick,
}: {
  paper: PaperListItem;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full rounded-md border p-3 text-left transition ${
        active ? 'border-moss bg-mint/45' : 'border-ink/10 bg-white hover:border-moss/50'
      }`}
    >
      <div className="line-clamp-2 text-sm font-medium text-ink">{paper.originalFilename}</div>
      <div className="mt-2 flex items-center gap-2 text-xs text-moss">
        <StatusIcon status={paper.status} />
        {paper.status}
      </div>
    </button>
  );
}

function StatusIcon({ status }: { status: PaperListItem['status'] }) {
  if (status === 'completed') return <CheckCircle2 className="h-4 w-4 text-moss" />;
  if (status === 'failed') return <XCircle className="h-4 w-4 text-rust" />;
  if (status === 'processing') return <Loader2 className="h-4 w-4 animate-spin text-gold" />;
  return <Clock3 className="h-4 w-4 text-moss" />;
}

function PaperWorkspace({ paperId }: { paperId: string }) {
  const paperQuery = useQuery({
    queryKey: ['paper', paperId],
    queryFn: () => getPaper(paperId),
    refetchInterval: (query) => {
      const status = query.state.data?.paper?.status;
      return status === 'completed' || status === 'failed' ? false : 3000;
    },
  });

  const graphQuery = useQuery({
    queryKey: ['graph', paperId],
    queryFn: () => getGraph(paperId),
    enabled: paperQuery.data?.paper?.status === 'completed',
  });

  const analysis = paperQuery.data?.analysis;
  const references = paperQuery.data?.references ?? [];

  if (paperQuery.isLoading) {
    return <div className="rounded-lg border border-ink/10 bg-white/70 p-6">Loading paper...</div>;
  }

  return (
    <section className="space-y-5">
      <div className="rounded-lg border border-ink/10 bg-white/75 p-5 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-md bg-mint px-2 py-1 text-xs font-medium text-moss">
              <StatusIcon status={paperQuery.data.paper.status} />
              {paperQuery.data.paper.status}
            </div>
            <h2 className="max-w-4xl text-2xl font-semibold tracking-normal text-ink">
              {analysis?.title || paperQuery.data.paper.originalFilename}
            </h2>
            <p className="mt-2 text-sm text-moss">
              {(analysis?.authors ?? []).length ? analysis.authors.join(', ') : 'Authors will appear after extraction.'}
            </p>
          </div>
        </div>
        {paperQuery.data.paper.status !== 'completed' && (
          <p className="mt-4 rounded-md bg-paper p-3 text-sm text-moss">
            The worker is processing extraction, reference parsing, chunking, and analysis.
          </p>
        )}
        {paperQuery.data.paper.errorMessage && (
          <p className="mt-4 rounded-md bg-rust/10 p-3 text-sm text-rust">{paperQuery.data.paper.errorMessage}</p>
        )}
      </div>

      {analysis && (
        <>
          <AnalysisGrid analysis={analysis} />
          <QuestionPanel paperId={paperId} />
          <ReferenceGraph graph={graphQuery.data} />
          <ReferenceList references={references} />
        </>
      )}
    </section>
  );
}

function AnalysisGrid({ analysis }: { analysis: any }) {
  const fields = [
    ['Simple Explanation', analysis.simpleSummary, Brain],
    ['Problem Statement', analysis.problemStatement, FileText],
    ['Objective', analysis.researchObjective, GitBranch],
    ['Methodology', analysis.methodology, Brain],
    ['Dataset', analysis.dataset, FileText],
    ['Algorithms / Models', analysis.algorithms, Brain],
    ['Results', analysis.results, CheckCircle2],
    ['Limitations', analysis.limitations, XCircle],
    ['Conclusion', analysis.conclusion, FileText],
  ];

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
      {fields.map(([title, value, Icon]) => (
        <article key={title as string} className="rounded-lg border border-ink/10 bg-white/75 p-4 shadow-soft">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-graphite">
            <Icon className="h-4 w-4 text-moss" />
            {title as string}
          </div>
          <p className="text-sm leading-6 text-ink/80">{(value as string) || 'Not detected yet.'}</p>
        </article>
      ))}
    </div>
  );
}

function QuestionPanel({ paperId }: { paperId: string }) {
  const [question, setQuestion] = useState('What is the main contribution?');
  const [answer, setAnswer] = useState<any>(null);
  const mutation = useMutation({
    mutationFn: () => askQuestion(paperId, question),
    onSuccess: setAnswer,
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <section className="rounded-lg border border-ink/10 bg-white/75 p-4 shadow-soft">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-graphite">
        <MessageSquareText className="h-4 w-4 text-moss" />
        Ask This Paper
      </div>
      <form onSubmit={onSubmit} className="flex flex-col gap-3 md:flex-row">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          className="min-h-11 flex-1 rounded-md border border-ink/15 bg-paper px-3 text-sm outline-none focus:border-moss"
        />
        <button
          type="submit"
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-md bg-moss px-4 text-sm font-medium text-white"
        >
          {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <MessageSquareText className="h-4 w-4" />}
          Ask
        </button>
      </form>
      {answer && (
        <div className="mt-4 rounded-md bg-paper p-4 text-sm leading-6 text-ink/85">
          <p>{answer.answer}</p>
          <div className="mt-3 text-xs font-medium text-moss">
            Sources: {answer.sources?.map((source: any) => source.sectionName).join(', ') || 'paper chunks'}
          </div>
        </div>
      )}
    </section>
  );
}

function ReferenceGraph({ graph }: { graph: any }) {
  const nodes = useMemo(() => graph?.nodes ?? [], [graph]);
  const edges = useMemo(() => graph?.edges ?? [], [graph]);

  return (
    <section className="rounded-lg border border-ink/10 bg-white/75 p-4 shadow-soft">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-graphite">
        <GitBranch className="h-4 w-4 text-moss" />
        Citation Relationship Graph
      </div>
      <div className="h-[420px] rounded-md border border-ink/10 bg-paper">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </section>
  );
}

function ReferenceList({ references }: { references: any[] }) {
  return (
    <section className="rounded-lg border border-ink/10 bg-white/75 p-4 shadow-soft">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-graphite">
        <GitBranch className="h-4 w-4 text-moss" />
        References
      </div>
      <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
        {references.length ? (
          references.map((reference) => (
            <article key={reference.id} className="rounded-md border border-ink/10 bg-paper p-3">
              <div className="text-sm font-semibold text-ink">
                [{reference.citationKey}] {reference.title || 'Untitled reference'}
              </div>
              <div className="mt-1 text-xs text-moss">
                {reference.year || 'Year unknown'} - {reference.relationship} - importance {reference.importance}/10
              </div>
              <p className="mt-2 line-clamp-3 text-xs leading-5 text-ink/70">{reference.rawText}</p>
            </article>
          ))
        ) : (
          <p className="rounded-md bg-paper p-3 text-sm text-moss">No references detected yet.</p>
        )}
      </div>
    </section>
  );
}

function EmptyWorkspace() {
  return (
    <section className="rounded-lg border border-dashed border-moss/40 bg-white/70 p-8 text-center shadow-soft">
      <Upload className="mx-auto h-10 w-10 text-moss" />
      <h2 className="mt-4 text-xl font-semibold tracking-normal">Upload a paper to begin</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-moss">
        The first pipeline extracts text, detects paper sections, parses references, creates chunks, and prepares the paper for question answering.
      </p>
    </section>
  );
}
