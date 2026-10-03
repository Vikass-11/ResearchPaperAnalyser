import asyncio
import logging
from typing import List, Dict, Any
from .models import AcademicPaper
from .utils import deduplicate_papers
from .openalex_service import search_openalex
from .semantic_scholar_service import search_semantic_scholar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def search_academic_papers(query: str, limit: int = 10) -> Dict[str, Any]:
    logger.info(f"[ACADEMIC_SEARCH] Query: {query}")
    
    # Run searches in parallel
    openalex_task = search_openalex(query, limit=limit)
    semantic_task = search_semantic_scholar(query, limit=limit)
    
    openalex_results, semantic_results = await asyncio.gather(
        openalex_task, semantic_task, return_exceptions=True
    )
    
    if isinstance(openalex_results, Exception):
        logger.error(f"[ACADEMIC_SEARCH] OpenAlex failed: {openalex_results}")
        openalex_results = []
    
    if isinstance(semantic_results, Exception):
        logger.error(f"[ACADEMIC_SEARCH] Semantic Scholar failed: {semantic_results}")
        semantic_results = []
        
    logger.info(f"[OPENALEX] Returned {len(openalex_results)} results")
    logger.info(f"[SEMANTIC_SCHOLAR] Returned {len(semantic_results)} results")
    
    combined = openalex_results + semantic_results
    logger.info(f"[ACADEMIC_SEARCH] Combined results: {len(combined)}")
    
    deduplicated = deduplicate_papers(combined)
    
    # Sort by citation count (descending) and trim to limit
    deduplicated = sorted(deduplicated, key=lambda x: x.citation_count, reverse=True)[:limit]
    
    logger.info(f"[ACADEMIC_SEARCH] After deduplication: {len(deduplicated)}")
    
    return {
        "query": query,
        "total": len(deduplicated),
        "providers": {
            "openalex": len([p for p in deduplicated if p.source == "OpenAlex"]),
            "semantic_scholar": len([p for p in deduplicated if p.source == "Semantic Scholar"])
        },
        "results": [p.dict() for p in deduplicated]
    }
