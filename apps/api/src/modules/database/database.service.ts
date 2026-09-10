import { Injectable, OnModuleDestroy, OnModuleInit } from '@nestjs/common';
import { Pool, QueryResult, QueryResultRow } from 'pg';

@Injectable()
export class DatabaseService implements OnModuleInit, OnModuleDestroy {
  private readonly pool = new Pool({
    connectionString: process.env.DATABASE_URL,
  });

  async onModuleInit() {
    await this.ensureSchema();
  }

  async onModuleDestroy() {
    await this.pool.end();
  }

  async query<T extends QueryResultRow = QueryResultRow>(
    text: string,
    params: unknown[] = [],
  ): Promise<QueryResult<T>> {
    return this.pool.query<T>(text, params);
  }

  private async ensureSchema() {
    await this.pool.query(`CREATE EXTENSION IF NOT EXISTS vector;`);
    await this.pool.query(`CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`);

    await this.pool.query(`
      CREATE TABLE IF NOT EXISTS papers (
        id UUID PRIMARY KEY,
        original_filename TEXT NOT NULL,
        storage_path TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'queued',
        error_message TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS paper_analyses (
        paper_id UUID PRIMARY KEY REFERENCES papers(id) ON DELETE CASCADE,
        title TEXT,
        authors TEXT[] NOT NULL DEFAULT '{}',
        abstract TEXT,
        keywords TEXT[] NOT NULL DEFAULT '{}',
        simple_summary TEXT,
        technical_summary TEXT,
        problem_statement TEXT,
        research_objective TEXT,
        methodology TEXT,
        dataset TEXT,
        algorithms TEXT,
        results TEXT,
        limitations TEXT,
        conclusion TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS paper_files (
        paper_id UUID PRIMARY KEY REFERENCES papers(id) ON DELETE CASCADE,
        pdf_data BYTEA NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS paper_sections (
        id BIGSERIAL PRIMARY KEY,
        paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        content TEXT NOT NULL,
        order_index INTEGER NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS paper_chunks (
        id BIGSERIAL PRIMARY KEY,
        paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
        section_name TEXT NOT NULL,
        content TEXT NOT NULL,
        token_estimate INTEGER NOT NULL,
        embedding VECTOR(768),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS paper_references (
        id BIGSERIAL PRIMARY KEY,
        paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
        citation_key TEXT,
        title TEXT,
        authors TEXT[] NOT NULL DEFAULT '{}',
        year TEXT,
        raw_text TEXT NOT NULL,
        relationship TEXT NOT NULL DEFAULT 'referenced work',
        importance INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS qa_history (
        id BIGSERIAL PRIMARY KEY,
        paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        sources JSONB NOT NULL DEFAULT '[]'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
      );
    `);
  }
}
