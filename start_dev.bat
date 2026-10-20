@echo off
echo ========================================================
echo  Starting ScholarGraph AI / ResearchPaperAnalyzer
echo ========================================================

echo Starting FastAPI Backend on http://localhost:8000 ...
start "ScholarGraph Backend" cmd /k "cd backend && ..\venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo Starting Vite Frontend on http://localhost:5173 ...
start "ScholarGraph Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 3 >nul
start http://localhost:5173

echo ========================================================
echo  ScholarGraph AI is booting up!
echo  - Frontend: http://localhost:5173
echo  - Backend API: http://localhost:8000
echo  - Swagger Docs: http://localhost:8000/docs
echo ========================================================
