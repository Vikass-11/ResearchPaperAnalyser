import os
import json
import logging
import asyncio
import traceback
from typing import Dict, Any, List
from pydantic import ValidationError
from datetime import datetime

from app.models.database import SessionLocal
from app.models.schema import ResearchProfile, RelatedPaper, LiteratureAnalysis
from app.schemas.literature_analysis import LiteratureAnalysisSchema
from app.services.literature.research_profile_service import normalize_list_field

logger = logging.getLogger(__name__)

MAX_DETAILED_ANALYSIS_PAPERS = int(os.getenv("MAX_DETAILED_ANALYSIS_PAPERS", "10"))
LITERATURE_ANALYSIS_CONCURRENCY = int(os.getenv("LITERATURE_ANALYSIS_CONCURRENCY", "2"))

semaphore = asyncio.Semaphore(LITERATURE_ANALYSIS_CONCURRENCY)

PROMPT_TEMPLATE = """You are analyzing a RELATED academic paper for a research literature review.

CRITICAL INSTRUCTION:
You must describe the RELATED PAPER Information in your output (problem, objective, methods, etc).
Do NOT copy or describe the TARGET RESEARCH PROFILE in these fields. The Target Research Profile is provided SOLELY so you can compare the related paper to it in the 'similarities', 'differences', and 'relevance_to_target' fields.

Analyze ONLY information supported by the supplied RELATED PAPER metadata/abstract.
Do not invent details.
If a field cannot be determined from the provided RELATED PAPER information, return an empty list [] for array fields, or "Not available from retrieved metadata." for string fields.
Return structured JSON matching the supplied schema.

--- Target Research Profile ---
Topic: {target_topic}
Problem: {target_problem}
Objective: {target_objective}
Methodology: {target_methodology}
Methods: {target_methods}
Algorithms: {target_algorithms}
Models: {target_models}
Technologies: {target_technologies}
Datasets: {target_datasets}
Key Concepts: {target_concepts}
Keywords: {target_keywords}

--- Related Paper Information ---
Title: {paper_title}
Authors: {paper_authors}
Year: {paper_year}
Venue: {paper_venue}
Keywords: {paper_keywords}
Abstract: {paper_abstract}
Type: {paper_type}

Ensure you output valid JSON matching the specified schema format.
"""

async def analyze_single_paper(paper_id: int, cand_id: int, target_context: dict, cand_context: dict) -> dict:
    async with semaphore:
        logger.info(f"[LIT_ANALYSIS] Starting analysis for RelatedPaper {cand_id}")
        
        prompt = PROMPT_TEMPLATE.format(
            target_topic=target_context.get("topic", "N/A"),
            target_problem=target_context.get("problem", "N/A"),
            target_objective=target_context.get("objective", "N/A"),
            target_methodology=target_context.get("methodology", "N/A"),
            target_methods=target_context.get("methods", "N/A"),
            target_algorithms=target_context.get("algorithms", "N/A"),
            target_models=target_context.get("models", "N/A"),
            target_technologies=target_context.get("technologies", "N/A"),
            target_datasets=target_context.get("datasets", "N/A"),
            target_concepts=target_context.get("concepts", "N/A"),
            target_keywords=target_context.get("keywords", "N/A"),
            
            paper_title=cand_context.get("title", "N/A"),
            paper_authors=cand_context.get("authors", "N/A"),
            paper_year=cand_context.get("year", "N/A"),
            paper_venue=cand_context.get("venue", "N/A"),
            paper_keywords=cand_context.get("keywords", "N/A"),
            paper_abstract=cand_context.get("abstract", "N/A"),
            paper_type=cand_context.get("paper_type", "N/A")
        )
        
        try:
            from app.services.llm_provider import client, LLM_MODEL
            response = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                tools=[{
                    "type": "function",
                    "function": {
                        "name": "submit_literature_analysis",
                        "description": "Submit literature analysis",
                        "parameters": LiteratureAnalysisSchema.model_json_schema()
                    }
                }],
                tool_choice={"type": "function", "function": {"name": "submit_literature_analysis"}},
                temperature=0.2
            )
            
            tool_call = response.choices[0].message.tool_calls[0]
            result_json = json.loads(tool_call.function.arguments)
            
            if not result_json:
                raise ValueError("Failed to parse JSON from LLM response.")
            
            # Normalize list fields for llama3.2 which sometimes returns stringified lists
            list_fields = [
                "methods", "algorithms", "models", "datasets", "key_findings",
                "contributions", "limitations", "strengths", "weaknesses",
                "similarities", "differences"
            ]
            
            for field in list_fields:
                if field in result_json:
                    result_json[field] = normalize_list_field(result_json.get(field))
            
            # Validate with schema
            validated = LiteratureAnalysisSchema(**result_json)
            
            return {
                "status": "success",
                "related_paper_id": cand_id,
                "data": validated.model_dump()
            }
        except Exception as e:
            logger.error(f"[LIT_ANALYSIS] Error analyzing RelatedPaper {cand_id}: {e}")
            logger.debug(traceback.format_exc())
            return {
                "status": "failed",
                "related_paper_id": cand_id,
                "error": str(e)
            }

async def analyze_related_papers(paper_id: int) -> Dict[str, Any]:
    logger.info(f"[LIT_ANALYSIS] Starting Phase 7 for paper {paper_id}")
    
    db = SessionLocal()
    try:
        profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
        if not profile:
            logger.error("[LIT_ANALYSIS] Research profile not found.")
            return {"error": "Research profile must be generated before detailed literature analysis."}
            
        related_papers = (
            db.query(RelatedPaper)
            .filter(RelatedPaper.source_paper_id == paper_id)
            .filter(RelatedPaper.relevance_score.isnot(None))
            .filter(RelatedPaper.title.isnot(None))
            .order_by(RelatedPaper.relevance_score.desc())
            .limit(MAX_DETAILED_ANALYSIS_PAPERS)
            .all()
        )
        
        if not related_papers:
            return {
                "paper_id": paper_id,
                "status": "completed",
                "papers_selected": 0,
                "papers_analyzed": 0,
                "papers_failed": 0
            }
            
        target_context = {
            "topic": profile.research_topic,
            "problem": profile.research_problem,
            "objective": profile.research_objective,
            "methodology": profile.methodology,
            "methods": profile.methods,
            "algorithms": profile.algorithms,
            "models": profile.models,
            "technologies": profile.technologies,
            "datasets": profile.datasets,
            "concepts": profile.key_concepts,
            "keywords": profile.keywords
        }
        
        tasks = []
        for cand in related_papers:
            cand_context = {
                "title": cand.title,
                "authors": cand.authors,
                "year": cand.year,
                "venue": cand.venue,
                "keywords": cand.keywords,
                "abstract": cand.abstract,
                "paper_type": cand.paper_type
            }
            tasks.append(analyze_single_paper(paper_id, cand.id, target_context, cand_context))
            
        results = await asyncio.gather(*tasks)
        
        analyzed_count = 0
        failed_count = 0
        
        for res in results:
            if res["status"] == "success":
                cand_id = res["related_paper_id"]
                data = res["data"]
                
                existing = db.query(LiteratureAnalysis).filter(LiteratureAnalysis.related_paper_id == cand_id).first()
                if not existing:
                    new_analysis = LiteratureAnalysis(
                        related_paper_id=cand_id,
                        **data
                    )
                    db.add(new_analysis)
                else:
                    for k, v in data.items():
                        setattr(existing, k, v)
                    existing.updated_at = datetime.utcnow()
                analyzed_count += 1
            else:
                failed_count += 1
                
        db.commit()
        
        return {
            "paper_id": paper_id,
            "status": "completed",
            "papers_selected": len(related_papers),
            "papers_analyzed": analyzed_count,
            "papers_failed": failed_count
        }
    except Exception as e:
        logger.error(f"[LIT_ANALYSIS] Execution failed: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
