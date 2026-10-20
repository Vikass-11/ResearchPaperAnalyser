# Start ScholarGraph AI Backend and Frontend concurrently
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting ScholarGraph AI / ResearchPaperAnalyzer" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location backend; ..\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"

# Start Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location frontend; npm run dev"

Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Write-Host "Services started:" -ForegroundColor Yellow
Write-Host " - Frontend:    http://localhost:5173"
Write-Host " - Backend API: http://localhost:8000"
Write-Host " - API Docs:    http://localhost:8000/docs"
