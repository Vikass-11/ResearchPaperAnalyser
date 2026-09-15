# API Contracts

## Base URL: `/api/v1`

---

### Papers

#### **POST /papers/upload**
- **Request**: `multipart/form-data` containing `file` (PDF)
- **Response**: 
  ```json
  {
    "id": 1,
    "title": "Extracted Title",
    "status": "UPLOADED",
    "message": "Paper uploaded and processing started."
  }
  ```
- **Description**: Uploads a paper, saves the file, creates a DB record, and triggers the background processing pipeline.

#### **GET /papers**
- **Response**: 
  ```json
  [
    {
      "id": 1,
      "title": "Attention Is All You Need",
      "authors": ["Ashish Vaswani", "Noam Shazeer"],
      "year": 2017,
      "processing_status": "COMPLETED",
      "created_at": "2026-09-15T09:00:00Z"
    }
  ]
  ```
- **Description**: Lists all uploaded papers with their status.

#### **GET /papers/{paper_id}**
- **Response**: Full paper object including metadata, abstract, AI analysis (summary, methodology, results, contributions, limitations), and text sections (with evidence tracking).

#### **GET /papers/{paper_id}/references**
- **Response**: 
  ```json
  [
    {
      "id": 101,
      "reference_number": "[1]",
      "title": "Neural Machine Translation",
      "verification_status": "VERIFIED_CROSSREF",
      "doi": "10.xxx/yyy",
      "citation_count": 1500,
      "importance_score": 0.85
    }
  ]
  ```
- **Description**: Retrieves all extracted references for the paper.

#### **GET /papers/{paper_id}/citations**
- **Response**: 
  ```json
  [
    {
      "id": 50,
      "reference_id": 101,
      "context": "We base our architecture on [1]",
      "intent": "METHODOLOGY",
      "page_number": 4,
      "char_position": 1500
    }
  ]
  ```
- **Description**: Retrieves all in-text citation instances, their context, page-level evidence, and their classified intent.

#### **GET /papers/{paper_id}/citation-graph**
- **Response**: 
  ```json
  {
    "nodes": [
      { "id": "p1", "data": { "label": "Current Paper", "type": "main" } },
      { "id": "r101", "data": { "label": "Neural Machine Translation", "type": "reference" } }
    ],
    "edges": [
      { "id": "e1", "source": "r101", "target": "p1", "label": "METHODOLOGY" }
    ]
  }
  ```
- **Description**: Generates the citation relationship graph data for React Flow.

#### **GET /papers/{paper_id}/similar**
- **Response**: 
  ```json
  [
    {
      "title": "BERT: Pre-training of Deep Bidirectional Transformers",
      "doi": "10.arxiv/1810.04805",
      "similarity_score": 0.89,
      "reason": "Similar methodology and architecture."
    }
  ]
  ```
- **Description**: Returns similar papers found via OpenAlex and semantic vector search.

#### **GET /papers/{paper_id}/research-gaps**
- **Response**: 
  ```json
  [
    {
      "observation": "Evaluated on a single dataset.",
      "potential_gap": "Evaluate on multilingual datasets.",
      "evidence": { "section": "Limitations", "page_number": 8 }
    }
  ]
  ```
- **Description**: Returns AI-detected research gaps with specific evidence pointers.

#### **POST /papers/{paper_id}/chat**
- **Request**: 
  ```json
  {
    "message": "What is the main contribution?",
    "history": []
  }
  ```
- **Response**: 
  ```json
  {
    "answer": "The authors introduce the Transformer...",
    "evidence": [
      {
        "content": "We propose the Transformer...",
        "page_number": 1,
        "section": "Abstract"
      }
    ]
  }
  ```
- **Description**: Performs a grounded RAG query over the paper chunks and returns an answer with retrieved evidence.

---

### References

#### **GET /references/{reference_id}**
- **Response**: Detailed reference object including its verification status (Crossref/OpenAlex), global citation count, and AI summaries (why cited, relationship, contribution).

#### **POST /references/{reference_id}/analyze**
- **Response**: Triggers an on-demand deep LLM analysis of why this reference is important and updates the DB, returning the updated reference object.
