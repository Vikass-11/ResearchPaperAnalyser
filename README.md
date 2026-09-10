# ScholarGraph AI

ScholarGraph AI is a local-first research paper analyzer. It uploads a PDF, extracts structure and references, stores chunks for retrieval, answers paper questions, and shows a citation relationship graph.

## Day 1 Status

This repository starts with a deployable foundation:

- Next.js web app
- NestJS API
- BullMQ worker
- PostgreSQL schema designed for pgvector
- Redis-backed background processing
- PDF text extraction with heuristic paper analysis
- Optional Ollama integration hook
- GROBID service in Docker Compose for the next extraction upgrade

## Run Locally

1. Copy environment values:

```bash
cp .env.example .env
```

2. Start infrastructure:

```bash
docker compose up -d postgres redis grobid
```

3. Install dependencies:

```bash
npm install
```

4. Start the app, API, and worker:

```bash
npm run dev
```

Frontend: http://localhost:3000  
API: http://localhost:4000

## Optional Local AI

Start Ollama separately or with Docker Compose:

```bash
docker compose --profile ai up -d ollama
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

Then set:

```env
AI_PROVIDER=ollama
```

The app still works without Ollama using deterministic extraction and heuristic analysis.
