import os
import json
import logging
import re
from typing import Dict, Any, List
from datetime import datetime

from app.models.database import SessionLocal
from app.models.schema import Paper, ResearchProfile, ResearchGap, RelatedPaper, RecentResearch
from app.schemas.recent_research import RecentResearchSchema
from app.services.academic_search.academic_search_service import search_academic_papers
from app.services.llm_provider import client, LLM_MODEL

def safe_get_list(val):
    if not val:
        return []
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except:
            return [val]
    if isinstance(val, list):
        return val
    return []

logger = logging.getLogger(__name__)

RECENT_RESEARCH_YEARS = int(os.getenv("RECENT_RESEARCH_YEARS", "5"))
MAX_RECENT_RESEARCH_QUERIES = int(os.getenv("MAX_RECENT_RESEARCH_QUERIES", "5"))
MAX_RECENT_RESULTS_PER_QUERY = int(os.getenv("MAX_RECENT_RESULTS_PER_QUERY", "20"))
MAX_RECENT_RESEARCH_PAPERS = int(os.getenv("MAX_RECENT_RESEARCH_PAPERS", "30"))
MAX_RECENT_LLM_ANALYSIS = int(os.getenv("MAX_RECENT_LLM_ANALYSIS", "10"))

VALID_RELATIONSHIPS = [
    "Directly Related",
    "Methodologically Related",
    "Algorithmically Related",
    "Domain Related",
    "Addresses Research Gap",
    "Recent Development",
    "Alternative Approach",
    "Other Related"
]

def normalize_string(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r'[^\w\s]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def build_queries(profile: ResearchProfile, gaps: List[ResearchGap]) -> List[str]:
    queries = []
    
    topic = profile.research_topic or ""
    keywords = safe_get_list(profile.keywords)
    problem = profile.research_problem or ""
    methodology = profile.methodology or ""
    methods = safe_get_list(profile.methods)
    algorithms = safe_get_list(profile.algorithms)
    models = safe_get_list(profile.models)
    domain = profile.research_domain or ""
    
    # Query 1: research topic + main keywords
    q1 = f"{topic} {' '.join(keywords[:2])}".strip()
    if q1: queries.append(q1)
        
    # Query 2: research problem + methodology
    q2 = f"{problem} {methodology} {' '.join(methods[:2])}".strip()
    if q2: queries.append(q2)
        
    # Query 3: algorithms + models + domain
    q3 = f"{' '.join(algorithms[:2])} {' '.join(models[:2])} {domain}".strip()
    if q3: queries.append(q3)
        
    # Query 4: recent developments
    if topic:
        queries.append(f"{topic} recent developments")
        
    # Query 5: identified research gaps
    for gap in gaps[:2]:
        queries.append(f"{gap.title} {gap.gap_type}")
        
    # Deduplicate and limit
    valid_queries = []
    seen = set()
    for q in queries:
        if q and q not in seen:
            valid_queries.append(q)
            seen.add(q)
            
    return valid_queries[:MAX_RECENT_RESEARCH_QUERIES]


def calculate_recent_relevance(candidate: Dict[str, Any], profile: ResearchProfile, gaps: List[ResearchGap], current_year: int) -> tuple:
    title = candidate.get("title", "")
    abstract = candidate.get("abstract", "")
    text_corpus = f"{title} {abstract}".lower()
    
    # Text sets for similarity
    c_words = set(re.findall(r'\w+', text_corpus))
    
    # Profile components
    t_topic = set(re.findall(r'\w+', (profile.research_topic or "").lower()))
    t_prob = set(re.findall(r'\w+', (profile.research_problem or "").lower()))
    t_kw = set(re.findall(r'\w+', " ".join(safe_get_list(profile.keywords)).lower()))
    t_meth = set(re.findall(r'\w+', " ".join(safe_get_list(profile.methods) + [profile.methodology or ""]).lower()))
    t_alg = set(re.findall(r'\w+', " ".join(safe_get_list(profile.algorithms) + safe_get_list(profile.models)).lower()))
    t_dom = set(re.findall(r'\w+', (profile.research_domain or "").lower()))
    
    def score_overlap(target_set):
        if not target_set: return 0.0
        return len(target_set.intersection(c_words)) / min(len(target_set), max(len(c_words), 1))
        
    topic_sim = score_overlap(t_topic)
    prob_sim = score_overlap(t_prob)
    kw_sim = score_overlap(t_kw)
    meth_sim = score_overlap(t_meth)
    alg_sim = score_overlap(t_alg)
    dom_sim = score_overlap(t_dom)
    
    # Gap similarity
    gap_sim = 0.0
    matched_gaps = []
    for gap in gaps:
        g_words = set(re.findall(r'\w+', f"{gap.title} {gap.description}".lower()))
        sim = score_overlap(g_words)
        if sim > gap_sim:
            gap_sim = sim
        if sim > 0.15: # lexical threshold
            matched_gaps.append(gap.id)
            
    # Recency
    year = candidate.get("year", 0)
    recency_score = 0.0
    if year > 0 and year <= current_year:
        diff = current_year - year
        if diff < RECENT_RESEARCH_YEARS:
            # 2026 -> 1.0, 2025 -> 0.8, etc for window=5
            recency_score = max(0.0, 1.0 - (diff / RECENT_RESEARCH_YEARS))
            
    # Weights
    w_topic = 0.25
    w_prob = 0.20
    w_kw = 0.15
    w_meth = 0.10
    w_alg = 0.10
    w_dom = 0.10
    w_gap = 0.05
    w_recency = 0.05
    
    final_score = (
        topic_sim * w_topic +
        prob_sim * w_prob +
        kw_sim * w_kw +
        meth_sim * w_meth +
        alg_sim * w_alg +
        dom_sim * w_dom +
        gap_sim * w_gap +
        recency_score * w_recency
    )
    
    # Determine relationship
    if len(matched_gaps) > 0:
        relationship = "Addresses Research Gap"
        reason = "Addresses identified research gaps."
    elif alg_sim > 0.3:
        relationship = "Algorithmically Related"
        reason = "Uses highly similar algorithms/models."
    elif meth_sim > 0.3:
        relationship = "Methodologically Related"
        reason = "Shares significant methodological approach."
    elif topic_sim > 0.4 and recency_score >= 0.8:
        relationship = "Recent Development"
        reason = "Very recent paper on the exact same topic."
    elif topic_sim > 0.4 and prob_sim > 0.3:
        relationship = "Directly Related"
        reason = "Directly related to topic and problem."
    elif dom_sim > 0.4:
        relationship = "Domain Related"
        reason = "Operates in the same research domain."
    elif topic_sim > 0.2 and prob_sim < 0.1:
        relationship = "Alternative Approach"
        reason = "Similar topic but different problem approach."
    else:
        relationship = "Other Related"
        reason = "Generically related recent research."
        
    # Cap score
    final_score = min(1.0, max(0.0, final_score))
    
    return final_score, relationship, reason, matched_gaps

async def detect_recent_research(paper_id: int) -> Dict[str, Any]:
    logger.info(f"[RECENT_RESEARCH] Starting Phase 10 for paper {paper_id}")
    
    db = SessionLocal()
    
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return {"error": "Paper not found"}
            
        profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
        if not profile:
            return {"error": "Research profile must be generated before recent research discovery."}
            
        gaps = db.query(ResearchGap).filter(ResearchGap.paper_id == paper_id).all()
        
        # Determine recency window
        current_year = datetime.now().year
        min_year = current_year - RECENT_RESEARCH_YEARS + 1
        
        # Load exclusion sets
        target_title = normalize_string(paper.title)
        
        existing_related = db.query(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id).all()
        related_dois = set(p.doi.lower() for p in existing_related if p.doi)
        related_titles = set(normalize_string(p.title) for p in existing_related if p.title)
        
        # Queries
        queries = build_queries(profile, gaps)
        
        # Collect candidates
        candidates = []
        for q in queries:
            try:
                res = await search_academic_papers(q, limit=MAX_RECENT_RESULTS_PER_QUERY)
                candidates.extend(res.get("results", []))
            except Exception as e:
                logger.warning(f"Search failed for query '{q}': {e}")
                
        # Filter and Deduplicate
        seen_dois = set()
        seen_titles = set()
        
        valid_candidates = []
        for c in candidates:
            # Date filter
            year = c.get("year")
            if not year: continue
            try:
                year = int(year)
            except ValueError:
                continue
                
            if year < min_year or year > current_year:
                continue
                
            doi = (c.get("doi") or "").lower()
            title = normalize_string(c.get("title", ""))
            
            # Exclude uploaded
            if (title and title == target_title):
                continue
                
            # Exclude existing related papers
            if (doi and doi in related_dois) or (title and title in related_titles):
                continue
                
            # Deduplicate within candidates
            if (doi and doi in seen_dois) or (title and title in seen_titles):
                continue
                
            if doi: seen_dois.add(doi)
            if title: seen_titles.add(title)
            
            c["year"] = year
            valid_candidates.append(c)
            
        # Score and Build Schema
        scored_results = []
        for c in valid_candidates:
            score, rel_type, rel_reason, matched_gaps = calculate_recent_relevance(c, profile, gaps, current_year)
            
            authors = c.get("authors")
            if isinstance(authors, str):
                authors = [a.strip() for a in authors.split(",")]
            if not isinstance(authors, list):
                authors = []
                
            schema = RecentResearchSchema(
                external_id=c.get("external_id"),
                source=c.get("source"),
                title=c.get("title", "Unknown Title"),
                authors=authors,
                abstract=c.get("abstract"),
                year=c.get("year", current_year),
                doi=c.get("doi"),
                url=c.get("url"),
                venue=c.get("venue"),
                citation_count=c.get("citation_count"),
                relevance_score=score,
                relevance_reason=rel_reason,
                relationship_type=rel_type,
                is_newer_than_target=(c.get("year", current_year) > (paper.year or 1900)),
                addresses_gap=(len(matched_gaps) > 0),
                related_gap_ids=matched_gaps
            )
            scored_results.append(schema)
            
        # Sort and limit
        scored_results.sort(key=lambda x: x.relevance_score, reverse=True)
        scored_results = scored_results[:MAX_RECENT_RESEARCH_PAPERS]
        
        # Idempotent persistence
        db.query(RecentResearch).filter(RecentResearch.paper_id == paper_id).delete()
        
        for sr in scored_results:
            new_record = RecentResearch(
                paper_id=paper_id,
                **sr.model_dump()
            )
            db.add(new_record)
            
        db.commit()
        
        return {
            "paper_id": paper_id,
            "generated": True,
            "recent_research": [r.model_dump() for r in scored_results]
        }
        
    except Exception as e:
        logger.error(f"[RECENT_RESEARCH] Execution failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
