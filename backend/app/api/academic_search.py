from fastapi import APIRouter, Query
from app.services.academic_search import search_academic_papers

router = APIRouter()

@router.get("/academic-search")
async def perform_academic_search(q: str = Query(..., description="Search query"), limit: int = Query(10, description="Max results")):
    results = await search_academic_papers(q, limit)
    return results
