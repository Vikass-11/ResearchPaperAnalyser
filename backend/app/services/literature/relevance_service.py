import os
import re
import json
import logging
from typing import List, Dict, Any, Tuple, Set
from datetime import datetime
from app.models.database import SessionLocal
from app.models.schema import Paper, ResearchProfile, RelatedPaper

logger = logging.getLogger(__name__)

RECENT_PAPER_YEARS = int(os.getenv("RECENT_PAPER_YEARS", "5"))

STOP_WORDS = {
    "the", "a", "an", "and", "or", "of", "for", "to", "in", "on", "with",
    "using", "based", "approach", "method", "study", "analysis", "system",
    "evaluation", "comparative", "performance", "paper", "research",
    "model", "framework", "technique", "proposed", "novel", "new"
}

def normalize_text(text: str) -> str:
    if not text:
        return ""
    # Lowercase
    text = str(text).lower()
    # Remove punctuation
    text = re.sub(r'[^\w\s-]', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_tokens(text: str) -> Set[str]:
    norm = normalize_text(text)
    tokens = set()
    for word in norm.split():
        if len(word) > 1 and word not in STOP_WORDS:
            tokens.add(word)
    return tokens

def calculate_overlap(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union) if union else 0.0

def build_profile_context(profile: ResearchProfile) -> Dict[str, Set[str]]:
    def safe_list(val):
        if not val: return []
        if isinstance(val, list): return val
        return [val]

    topic_tokens = extract_tokens(profile.research_topic)
    problem_tokens = extract_tokens(profile.research_problem)
    
    method_tokens = extract_tokens(profile.methodology)
    for m in safe_list(profile.methods):
        method_tokens.update(extract_tokens(m))
        
    alg_model_tokens = set()
    for am in safe_list(profile.algorithms) + safe_list(profile.models):
        alg_model_tokens.update(extract_tokens(am))
        
    concept_tokens = set()
    for c in safe_list(profile.key_concepts):
        concept_tokens.update(extract_tokens(c))
        
    keyword_tokens = set()
    for kw in safe_list(profile.keywords):
        keyword_tokens.update(extract_tokens(kw))
        
    domain_tokens = extract_tokens(profile.research_domain)
    domain_tokens.update(extract_tokens(profile.application_domain))
    for sd in safe_list(profile.sub_domains):
        domain_tokens.update(extract_tokens(sd))
        
    return {
        "topic": topic_tokens,
        "problem": problem_tokens,
        "method": method_tokens,
        "algorithm": alg_model_tokens,
        "concept": concept_tokens,
        "keyword": keyword_tokens,
        "domain": domain_tokens
    }

def calculate_paper_relevance(cand: RelatedPaper, context: Dict[str, Set[str]]) -> Tuple[float, str, Dict[str, float]]:
    cand_text = f"{cand.title or ''} {cand.abstract or ''}"
    if cand.keywords:
        if isinstance(cand.keywords, list):
            cand_text += " " + " ".join(cand.keywords)
        else:
            cand_text += f" {cand.keywords}"
            
    cand_tokens = extract_tokens(cand_text)
    
    scores = {
        "topic": (calculate_overlap(context["topic"], cand_tokens) if context["topic"] else 0.0) * 100.0,
        "problem": (calculate_overlap(context["problem"], cand_tokens) if context["problem"] else 0.0) * 100.0,
        "keyword": (calculate_overlap(context["keyword"], cand_tokens) if context["keyword"] else 0.0) * 100.0,
        "method": (calculate_overlap(context["method"], cand_tokens) if context["method"] else 0.0) * 100.0,
        "algorithm": (calculate_overlap(context["algorithm"], cand_tokens) if context["algorithm"] else 0.0) * 100.0,
        "domain": (calculate_overlap(context["domain"], cand_tokens) if context["domain"] else 0.0) * 100.0,
        "concept": (calculate_overlap(context["concept"], cand_tokens) if context["concept"] else 0.0) * 100.0
    }
    
    current_year = datetime.now().year
    cand_year = cand.year or 0
    recency_score = 0.0
    if cand_year > 0 and (current_year - cand_year) <= RECENT_PAPER_YEARS:
        recency_score = (1.0 - ((current_year - cand_year) / (RECENT_PAPER_YEARS + 1))) * 100.0
        
    scores["recency"] = recency_score
    
    weights = {
        "topic": 0.25,
        "problem": 0.15,
        "keyword": 0.15,
        "method": 0.15,
        "algorithm": 0.10,
        "domain": 0.10,
        "concept": 0.05,
        "recency": 0.05
    }
    
    total_score = sum(scores[k] * weights[k] for k in weights)
    
    # Classification rules
    classification = "Other Related"
    
    is_recent = cand_year > 0 and (current_year - cand_year) <= RECENT_PAPER_YEARS
    is_old = cand_year > 0 and (current_year - cand_year) >= 10
    
    # Directly Related: strong topic/problem + method
    if scores["topic"] > 15.0 and scores["problem"] > 10.0 and (scores["method"] > 10.0 or scores["algorithm"] > 10.0):
        classification = "Directly Related"
    # Alternative Approach: similar problem, different method (method overlap is low)
    elif scores["problem"] > 15.0 and scores["method"] < 5.0 and scores["algorithm"] < 5.0:
        classification = "Alternative Approach"
    # Methodologically Related: strong method/algorithm, weak problem/domain
    elif (scores["method"] > 15.0 or scores["algorithm"] > 15.0) and scores["problem"] < 10.0:
        classification = "Methodologically Related"
    # Recent Development
    elif is_recent and (scores["topic"] > 10.0 or scores["method"] > 10.0):
        classification = "Recent Development"
    # Foundational
    elif is_old and (scores["method"] > 10.0 or scores["concept"] > 10.0):
        classification = "Foundational"
    # Domain Related
    elif scores["domain"] > 15.0:
        classification = "Domain Related"
        
    # Scale to 0-100 and round
    return min(100.0, round(total_score, 2)), classification, scores

def rank_related_papers(paper_id: int) -> Dict[str, Any]:
    logger.info(f"[RELEVANCE] Starting ranking for paper {paper_id}")
    
    db = SessionLocal()
    try:
        profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
        if not profile:
            logger.error("[RELEVANCE] Research profile must be generated before relevance ranking.")
            return {"error": "Research profile must be generated before relevance ranking."}
            
        related_papers = db.query(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id).all()
        if not related_papers:
            return {
                "paper_id": paper_id,
                "status": "completed",
                "papers_analyzed": 0,
                "top_relevance_score": 0.0
            }
            
        context = build_profile_context(profile)
        
        top_score = 0.0
        
        for cand in related_papers:
            score, category, breakdown = calculate_paper_relevance(cand, context)
            
            cand.relevance_score = score
            cand.relationship_type = category
            cand.score_breakdown = breakdown
            
            if score > top_score:
                top_score = score
                
        db.commit()
        
        logger.info(f"[RELEVANCE] Analyzed {len(related_papers)} papers. Top score: {top_score}")
        
        return {
            "paper_id": paper_id,
            "status": "completed",
            "papers_analyzed": len(related_papers),
            "top_relevance_score": top_score
        }
    except Exception as e:
        logger.error(f"[RELEVANCE] Error during ranking: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
