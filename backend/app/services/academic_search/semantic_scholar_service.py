import httpx
import asyncio
import logging
from typing import List
from .models import AcademicPaper
import os

from app.config import ACADEMIC_API_TIMEOUT_SECONDS, ACADEMIC_API_MAX_RETRIES

logger = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

async def search_semantic_scholar(query: str, limit: int = 10) -> List[AcademicPaper]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "paperId,title,abstract,year,authors,venue,citationCount,url,externalIds,publicationTypes"
    }
    
    headers = {}
    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY

    results = []
    
    async with httpx.AsyncClient(timeout=float(ACADEMIC_API_TIMEOUT_SECONDS)) as client:
        for attempt in range(ACADEMIC_API_MAX_RETRIES + 1):
            try:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 429:
                    logger.warning("Semantic Scholar rate limit hit, retrying...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                if response.status_code == 400:
                    logger.warning(f"Semantic Scholar Bad Request: {response.text}")
                    break
                response.raise_for_status()
                data = response.json()
                
                for item in data.get("data", []):
                    authors = [a.get("name") for a in item.get("authors", [])]
                    doi = item.get("externalIds", {}).get("DOI")
                    
                    paper = AcademicPaper(
                        external_id=item.get("paperId"),
                        source="Semantic Scholar",
                        title=item.get("title") or "Unknown Title",
                        authors=authors,
                        abstract=item.get("abstract"),
                        year=item.get("year"),
                        doi=doi,
                        url=item.get("url"),
                        venue=item.get("venue"),
                        citation_count=item.get("citationCount", 0),
                        paper_type=item.get("publicationTypes", [None])[0] if item.get("publicationTypes") else None,
                        raw_metadata=item
                    )
                    results.append(paper)
                break
            except httpx.RequestError as e:
                logger.error(f"Semantic Scholar RequestError: {e}")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Semantic Scholar Exception: {e}")
                break
                
    return results
