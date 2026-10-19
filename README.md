# ResearchPaperLens (ScholarGraph AI)

AI-Powered Research Paper Analysis, Citation Intelligence & Literature Discovery System.

ResearchPaperLens allows researchers to upload academic PDFs, automatically extract structure, parse citations, visualize citation networks, detect research gaps, synthesize community web reception, and discover recent related work using LLMs and academic search APIs.

---

## 🏗 Architecture & Tech Stack

- **Frontend:** React 19, Vite, Tailwind CSS, Lucide Icons, ForceGraph 2D (`react-force-graph-2d`).
- **Backend:** FastAPI (Python), SQLite (`scholargraph.db`), SQLAlchemy, PyMuPDF, Pydantic.
- **LLM Engine:** Groq (e.g. `openai/gpt-oss-120b`) for fast cloud inference or Ollama (`llama3.2`) for local offline inference via OpenAI-compatible async clients.
- **Academic APIs:** OpenAlex & Semantic Scholar integration for discovery, citation resolution, and relevance scoring.
- **Auxiliary Services (Optional):** GROBID container for enhanced PDF structure and TEI-XML extraction.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python:** 3.10+ (with virtual environment)
- **Node.js:** 18+ and npm
- **Docker:** (Optional, only needed if running GROBID or local Ollama)

---

### 2. Backend Setup

1. Open a terminal in the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv ..\venv
   ..\venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv ../venv
   source ../venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

   Configure your preferred LLM provider in `backend/.env`:
   - **Groq (Cloud - Recommended):**
     ```env
     LLM_PROVIDER=groq
     LLM_API_KEY=gsk_your_groq_api_key
     LLM_BASE_URL=https://api.groq.com/openai/v1
     LLM_MODEL=openai/gpt-oss-120b
     LLM_TIMEOUT_SECONDS=600
     LITERATURE_ANALYSIS_CONCURRENCY=1
     ```
   - **Ollama (Local):**
     ```env
     LLM_PROVIDER=ollama
     LLM_BASE_URL=http://localhost:11434/v1
     LLM_MODEL=llama3.2
     LLM_API_KEY=sk-placeholder
     ```

5. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - **API Docs (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Health Check:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### 3. Frontend Setup

1. Open a new terminal in the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Verify `frontend/.env`:
   ```env
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```

4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   - **Web App:** [http://localhost:5173](http://localhost:5173)

---

### 4. Optional Support Services (GROBID & Ollama)

To run GROBID for high-fidelity PDF extraction or local Ollama:
```bash
# Run GROBID
docker compose up -d grobid

# Run Ollama (optional)
docker compose --profile ai up -d ollama
ollama pull llama3.2
```

---

## 🧪 Running Tests

Run backend unit and integration tests from the `backend` directory:
```bash
cd backend
python -m pytest tests/test_api_integration.py tests/test_production_hardening.py
```

Run frontend build check:
```bash
cd frontend
npm run build
```

---

## 🌐 Production Deployment

- **Frontend (Vercel):**
  - Set Environment Variable: `VITE_API_BASE_URL=https://your-backend-domain.com/api/v1`
  - Ensure your backend `CORS_ORIGINS` includes your Vercel URL (e.g. `https://researchpaperlens.vercel.app`).
- **Backend:**
  - Can be hosted on platforms such as Render, Railway, Fly.io, or an AWS EC2 instance running Uvicorn.
