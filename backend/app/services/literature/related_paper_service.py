import os
import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from app.models.database import SessionLocal
from app.models.schema import Paper, ResearchProfile, RelatedPaper
from app.services.academic_search.academic_search_service import search_academic_papers
from app.services.academic_search.utils import normalize_title, normalize_doi

logger = logging.getLogger(__name__)

# Configurable settings
MAX_LITERATURE_QUERIES = int(os.getenv("MAX_LITERATURE_QUERIES", "5"))
MAX_RESULTS_PER_QUERY = int(os.getenv("MAX_RESULTS_PER_QUERY", "20"))
MAX_CANDIDATE_PAPERS = int(os.getenv("MAX_CANDIDATE_PAPERS", "100"))
MAX_STORED_RELATED_PAPERS = int(os.getenv("MAX_STORED_RELATED_PAPERS", "30"))

def clean_terms(terms: List[str]) -> List[str]:
    placeholders = {"not explicitly stated", "n/a", "none", "unknown", "not available", "not specified"}
    cleaned = []
    for term in terms:
        if not term: continue
        if isinstance(term, list):
            term = " ".join(str(t) for t in term)
        t = str(term).strip()
        if t.lower() not in placeholders and t:
            cleaned.append(t)
    # remove duplicate terms while preserving order
    unique = []
    seen = set()
    for c in cleaned:
        c_lower = c.lower()
        if c_lower not in seen:
            seen.add(c_lower)
            unique.append(c)
    return unique

def build_literature_queries(profile: ResearchProfile) -> List[str]:
    queries = []
    
    def add_query(terms: List[str]):
        cleaned = clean_terms(terms)
        if cleaned:
            # normalize whitespace and avoid excessively long queries
            query = " ".join(cleaned)
            query = " ".join(query.split())[:200]
            if query and query.lower() not in [q.lower() for q in queries]:
                queries.append(query)

    # 1. Research Topic
    add_query([profile.research_topic])
    
    # 2. Research Problem
    add_query([profile.research_problem])
    
    # 3. Methodology + Methods
    methods_list = profile.methods if isinstance(profile.methods, list) else []
    add_query([profile.methodology] + methods_list)
    
    # 4. Algorithms + Models + Key Concepts
    alg = profile.algorithms if isinstance(profile.algorithms, list) else []
    mod = profile.models if isinstance(profile.models, list) else []
    kc = profile.key_concepts if isinstance(profile.key_concepts, list) else []
    add_query(alg + mod + kc)
    
    # 5. Domain + Sub Domains + Application Domain + Keywords
    sub_dom = profile.sub_domains if isinstance(profile.sub_domains, list) else []
    kw = profile.keywords if isinstance(profile.keywords, list) else []
    add_query([profile.research_domain] + sub_dom + [profile.application_domain] + kw)
    
    return queries[:MAX_LITERATURE_QUERIES]

async def safe_search_academic_papers(query: str):
    try:
        results = await search_academic_papers(query, limit=MAX_RESULTS_PER_QUERY)
        for r in results.get("results", []):
            r["search_query"] = query
        return results
    except Exception as e:
        logger.error(f"[RELATED_PAPERS] Error searching for query '{query}': {e}")
        return {"total": 0, "results": [], "providers": {}}

async def discover_related_papers(paper_id: int) -> Dict[str, Any]:
    logger.info(f"[RELATED_PAPERS] Starting discovery for paper {paper_id}")
    
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return {"error": "Paper not found."}
            
        profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
        if not profile:
            logger.error("[RELATED_PAPERS] Research profile must be generated before related paper discovery.")
            return {"error": "Research profile must be generated before related paper discovery."}
            
        logger.info(f"[RELATED_PAPERS] Research topic: {profile.research_topic}")
        
        queries = build_literature_queries(profile)
        logger.info(f"[RELATED_PAPERS] Generated {len(queries)} queries")
        
        if not queries:
            return {
                "paper_id": paper_id,
                "status": "completed",
                "queries": 0,
                "candidates_found": 0,
                "papers_stored": 0
            }
            
        tasks = [safe_search_academic_papers(q) for q in queries]
        search_results = await asyncio.gather(*tasks)
        
        all_candidates = []
        providers_used = {"openalex": 0, "semantic_scholar": 0, "crossref": 0}
        
        for results in search_results:
            all_candidates.extend(results.get("results", []))
            for prov, count in results.get("providers", {}).items():
                providers_used[prov] = providers_used.get(prov, 0) + count
            
        total_candidates = len(all_candidates)
        logger.info(f"[RELATED_PAPERS] Combined candidates: {total_candidates}")
        
        # Filter uploaded paper and flag existing references
        source_doi = normalize_doi(getattr(paper, "doi", "")) if getattr(paper, "doi", None) else None
        source_title = normalize_title(paper.title) if paper.title else None
        
        existing_refs_dois = {normalize_doi(r.doi) for r in paper.references if getattr(r, "doi", None)}
        existing_refs_titles = {normalize_title(r.title) for r in paper.references if getattr(r, "title", None)}
        
        # Deduplicate candidates
        seen_dois = set()
        seen_titles_years = set()
        seen_provider_ids = set()
        deduplicated = []
        
        for cand in all_candidates:
            doi = normalize_doi(cand.get("doi", ""))
            title = normalize_title(cand.get("title", ""))
            year = cand.get("year")
            title_year = f"{title}_{year}" if title and year else title
            
            ext_id = cand.get("external_id")
            source = cand.get("source")
            prov_id = f"{source}_{ext_id}" if source and ext_id else None
            
            if not title:
                continue
                
            # Remove uploaded paper itself
            if doi and source_doi and doi == source_doi:
                continue
            if title and source_title and title == source_title:
                continue
            
            if doi and doi in seen_dois:
                continue
            if prov_id and prov_id in seen_provider_ids:
                continue
            if title_year and title_year in seen_titles_years:
                continue
                
            if doi: seen_dois.add(doi)
            if prov_id: seen_provider_ids.add(prov_id)
            if title_year: seen_titles_years.add(title_year)
            
            # Check existing references
            is_ref = False
            if doi and doi in existing_refs_dois:
                is_ref = True
            if title and title in existing_refs_titles:
                is_ref = True
                
            cand["is_existing_reference"] = is_ref
            
            deduplicated.append(cand)
            if len(deduplicated) >= MAX_CANDIDATE_PAPERS:
                break
                
        after_deduplication = len(deduplicated)
        logger.info(f"[RELATED_PAPERS] Candidates after deduplication/limit: {after_deduplication}")
        
        # Sort and limit stored papers
        final_candidates = sorted(deduplicated, key=lambda x: (
            bool(x.get("doi")), 
            x.get("citation_count", 0), 
            x.get("year", 0) or 0
        ), reverse=True)
        final_candidates = final_candidates[:MAX_STORED_RELATED_PAPERS]
        
        logger.info(f"[RELATED_PAPERS] Final candidates to store: {len(final_candidates)}")
        
        # Store in DB
        stored_count = 0
        for cand in final_candidates:
            c_doi = normalize_doi(cand.get("doi", ""))
            c_title = normalize_title(cand.get("title", ""))
            c_ext_id = cand.get("external_id")
            c_source = cand.get("source")
            
            query = db.query(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id)
            existing = None
            if c_doi:
                existing = query.filter(RelatedPaper.doi == c_doi).first()
            if not existing and c_ext_id and c_source:
                existing = query.filter(RelatedPaper.external_id == c_ext_id, RelatedPaper.source == c_source).first()
            
            if not existing:
                all_existing = query.all()
                for ex in all_existing:
                    if normalize_title(ex.title) == c_title:
                        existing = ex
                        break
                        
            if not existing:
                rp = RelatedPaper(
                    source_paper_id=paper_id,
                    external_id=c_ext_id,
                    title=cand.get("title", ""),
                    authors=cand.get("authors", []),
                    abstract=cand.get("abstract"),
                    year=cand.get("year"),
                    doi=cand.get("doi"),
                    url=cand.get("url"),
                    venue=cand.get("venue"),
                    citation_count=cand.get("citation_count", 0),
                    source=c_source,
                    paper_type=cand.get("paper_type"),
                    keywords=cand.get("keywords", []),
                    category="DISCOVERED",
                    is_existing_reference=cand.get("is_existing_reference", False),
                    search_query=cand.get("search_query")
                )
                db.add(rp)
                stored_count += 1
            else:
                existing.citation_count = cand.get("citation_count", 0)
                existing.is_existing_reference = cand.get("is_existing_reference", False)
                if not getattr(existing, "search_query", None) and cand.get("search_query"):
                    existing.search_query = cand.get("search_query")
                
        db.commit()
        logger.info(f"[RELATED_PAPERS] Stored {stored_count} related papers")
        
        return {
            "paper_id": paper_id,
            "status": "completed",
            "queries": len(queries),
            "candidates_found": after_deduplication,
            "papers_stored": stored_count
        }
        
    except Exception as e:
        logger.error(f"[RELATED_PAPERS] Discovery failed: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
