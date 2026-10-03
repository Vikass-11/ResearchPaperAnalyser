import httpx
import asyncio
import logging
from typing import List
from .models import AcademicPaper
import os

from app.config import ACADEMIC_API_TIMEOUT_SECONDS, ACADEMIC_API_MAX_RETRIES

logger = logging.getLogger(__name__)

OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL", "")

async def search_openalex(query: str, limit: int = 10) -> List[AcademicPaper]:
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per-page": limit,
    }
    if OPENALEX_EMAIL:
        params["mailto"] = OPENALEX_EMAIL

    results = []
    
    async with httpx.AsyncClient(timeout=float(ACADEMIC_API_TIMEOUT_SECONDS)) as client:
        for attempt in range(ACADEMIC_API_MAX_RETRIES + 1):
            try:
                response = await client.get(url, params=params)
                if response.status_code == 429:
                    logger.warning("OpenAlex rate limit hit, retrying...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                data = response.json()
                
                for item in data.get("results", []):
                    authors = [auth.get("author", {}).get("display_name") for auth in item.get("authorships", []) if auth.get("author", {}).get("display_name")]
                    
                    abstract = None
                    inv_abs = item.get("abstract_inverted_index")
                    if inv_abs:
                        word_index = []
                        for word, positions in inv_abs.items():
                            for pos in positions:
                                word_index.append((pos, word))
                        word_index.sort(key=lambda x: x[0])
                        abstract = " ".join([w[1] for w in word_index])
                        
                    paper = AcademicPaper(
                        external_id=item.get("id"),
                        source="OpenAlex",
                        title=item.get("title") or "Unknown Title",
                        authors=authors,
                        abstract=abstract,
                        year=item.get("publication_year"),
                        doi=item.get("doi"),
                        url=item.get("primary_location", {}).get("landing_page_url") if item.get("primary_location") else None,
                        venue=item.get("primary_location", {}).get("source", {}).get("display_name") if item.get("primary_location") and item.get("primary_location").get("source") else None,
                        citation_count=item.get("cited_by_count", 0),
                        paper_type=item.get("type"),
                        keywords=[kw.get("display_name") for kw in item.get("concepts", [])],
                        raw_metadata=item
                    )
                    results.append(paper)
                break
            except httpx.RequestError as e:
                logger.error(f"OpenAlex RequestError: {e}")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"OpenAlex Exception: {e}")
                break
                
    return results
