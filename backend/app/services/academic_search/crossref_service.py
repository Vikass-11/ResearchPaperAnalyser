import httpx
import asyncio
import logging
from typing import Optional
from .models import AcademicPaper
import os

logger = logging.getLogger(__name__)

CROSSREF_EMAIL = os.getenv("CROSSREF_EMAIL", "")

async def verify_doi_crossref(doi: str) -> Optional[AcademicPaper]:
    url = f"https://api.crossref.org/works/{doi}"
    params = {}
    if CROSSREF_EMAIL:
        params["mailto"] = CROSSREF_EMAIL

    async with httpx.AsyncClient(timeout=15.0) as client:
        for attempt in range(3):
            try:
                response = await client.get(url, params=params)
                if response.status_code == 429:
                    await asyncio.sleep(2 ** attempt)
                    continue
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json().get("message", {})
                
                authors = []
                for auth in data.get("author", []):
                    name_parts = []
                    if "given" in auth: name_parts.append(auth["given"])
                    if "family" in auth: name_parts.append(auth["family"])
                    if name_parts:
                        authors.append(" ".join(name_parts))
                
                year = None
                published = data.get("published-print") or data.get("published-online")
                if published and "date-parts" in published and published["date-parts"]:
                    year = published["date-parts"][0][0]
                    
                venue = None
                if "container-title" in data and data["container-title"]:
                    venue = data["container-title"][0]
                
                return AcademicPaper(
                    external_id=doi,
                    source="Crossref",
                    title=data.get("title", [""])[0],
                    authors=authors,
                    year=year,
                    doi=doi,
                    url=data.get("URL"),
                    venue=venue,
                    citation_count=data.get("is-referenced-by-count", 0),
                    paper_type=data.get("type"),
                    raw_metadata=data
                )
            except httpx.RequestError as e:
                logger.error(f"Crossref RequestError: {e}")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Crossref Exception: {e}")
                break
    return None
