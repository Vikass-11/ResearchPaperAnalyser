import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from pydantic import ValidationError

from app.models.database import SessionLocal
from app.models.schema import ResearchProfile, RelatedPaper, LiteratureAnalysis, LiteratureSurvey
from app.schemas.literature_survey import LiteratureSurveySchema
from app.services.llm_provider import client, LLM_MODEL
from app.services.literature.research_profile_service import normalize_list_field

logger = logging.getLogger(__name__)

MAX_SURVEY_PAPERS = int(os.getenv("MAX_SURVEY_PAPERS", "10"))

PROMPT_TEMPLATE = """You are generating an academic literature survey.

You are given:
1. The target research profile.
2. Structured analyses of related academic papers.

Use ONLY the supplied information.
Do not invent:
- datasets
- algorithms
- numerical results
- experimental results
- citations
- limitations
- future work

Synthesize the papers rather than writing one isolated summary per paper.
Return ONLY the requested structured fields.
Each field must contain concise academic prose.
For themes_text, return a simple list of theme names.
If information is unavailable, write: "Not available from retrieved metadata."

--- Target Research Profile ---
Topic: {target_topic}
Problem: {target_problem}
Objective: {target_objective}
Methodology: {target_methodology}
Methods: {target_methods}
Algorithms: {target_algorithms}
Models: {target_models}
Domain: {target_domain}
Keywords: {target_keywords}

--- Related Literature Analyses ---
{literature_context}
"""

RETRY_PROMPT = """Return ONLY valid JSON.
Do not include markdown.
Do not include explanations.
Do not include nested objects.
Return all required fields."""

async def call_llm(prompt: str, retry: bool = False):
    messages = [{"role": "user", "content": prompt}]
    if retry:
        messages.append({"role": "user", "content": RETRY_PROMPT})
        
    from app.schemas.literature_survey import LiteratureSurveyLLMResponse
    
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=[{
            "type": "function",
            "function": {
                "name": "submit_literature_survey",
                "description": "Submit literature survey",
                "parameters": LiteratureSurveyLLMResponse.model_json_schema()
            }
        }],
        tool_choice={"type": "function", "function": {"name": "submit_literature_survey"}},
        temperature=0.3
    )
    
    tool_call = response.choices[0].message.tool_calls[0]
    return json.loads(tool_call.function.arguments)

async def generate_literature_survey(paper_id: int) -> Dict[str, Any]:
    logger.info(f"[LIT_SURVEY] Starting Phase 8 for paper {paper_id}")
    
    db = SessionLocal()
    try:
        profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
        if not profile:
            logger.error("[LIT_SURVEY] Research profile not found.")
            return {"error": "Research profile must be generated before literature survey."}
            
        analyses = (
            db.query(LiteratureAnalysis)
            .join(RelatedPaper, LiteratureAnalysis.related_paper_id == RelatedPaper.id)
            .filter(RelatedPaper.source_paper_id == paper_id)
            .order_by(RelatedPaper.relevance_score.desc())
            .limit(MAX_SURVEY_PAPERS)
            .all()
        )
        
        if not analyses:
            logger.error("[LIT_SURVEY] No detailed literature analysis found.")
            return {"error": "Detailed literature analysis (Phase 7) must be completed before generating a survey."}
            
        target_context = {
            "target_topic": profile.research_topic or "N/A",
            "target_problem": profile.research_problem or "N/A",
            "target_objective": profile.research_objective or "N/A",
            "target_methodology": profile.methodology or "N/A",
            "target_methods": profile.methods or "N/A",
            "target_algorithms": profile.algorithms or "N/A",
            "target_models": profile.models or "N/A",
            "target_domain": profile.research_domain or "N/A",
            "target_keywords": profile.keywords or "N/A",
        }
        
        lit_context_strs = []
        for a in analyses:
            rp = a.related_paper
            lit_context_strs.append(f"""
Paper ID: {rp.id}
Title: {rp.title}
Year: {rp.year}
Relevance Score: {rp.relevance_score}
Relationship Type: {rp.relationship_type}
Problem: {a.problem_statement}
Objective: {a.objective}
Methodology: {a.methodology}
Methods: {a.methods}
Algorithms: {a.algorithms}
Key Findings: {a.key_findings}
Contributions: {a.contributions}
Limitations: {a.limitations}
Similarities: {a.similarities}
Differences: {a.differences}
            """.strip())
            
        literature_context = "\n\n---\n\n".join(lit_context_strs)
        
        prompt = PROMPT_TEMPLATE.format(
            **target_context,
            literature_context=literature_context
        )
        
        try:
            try:
                result_json = await call_llm(prompt, retry=False)
            except Exception as e:
                logger.warning(f"[LIT_SURVEY] LLM call failed, retrying: {e}")
                result_json = await call_llm(prompt, retry=True)
            
            if not result_json:
                raise ValueError("Failed to parse JSON from LLM response.")
            
            # Normalize list fields BEFORE validating with Pydantic
            result_json["themes_text"] = normalize_list_field(result_json.get("themes_text"))
            result_json["similarities"] = normalize_list_field(result_json.get("similarities"))
            result_json["differences"] = normalize_list_field(result_json.get("differences"))
            
            from app.schemas.literature_survey import LiteratureSurveyLLMResponse, LiteratureTheme
            
            llm_response = LiteratureSurveyLLMResponse(**result_json)
            
            themes_text = llm_response.themes_text
            similarities = llm_response.similarities
            differences = llm_response.differences
            
            # Construct LiteratureTheme objects
            themes = []
            for t_text in themes_text:
                if t_text and isinstance(t_text, str):
                    themes.append({"name": t_text.strip(), "description": t_text.strip()})
                    
            final_data = {
                "research_context": llm_response.research_context or "Not available from retrieved metadata.",
                "research_landscape": llm_response.research_landscape or "Not available from retrieved metadata.",
                "methodological_comparison": llm_response.methodological_comparison or "Not available from retrieved metadata.",
                "algorithm_model_comparison": llm_response.algorithm_model_comparison or "Not available from retrieved metadata.",
                "findings_synthesis": llm_response.findings_synthesis or "Not available from retrieved metadata.",
                "research_evolution": llm_response.research_evolution or "Not available from retrieved metadata.",
                "target_comparison": llm_response.target_comparison or "Not available from retrieved metadata.",
                "overall_synthesis": llm_response.overall_synthesis or "Not available from retrieved metadata.",
                "themes": themes,
                "similarities": similarities,
                "differences": differences
            }
                        
            validated = LiteratureSurveySchema(**final_data)
            
            existing = db.query(LiteratureSurvey).filter(LiteratureSurvey.paper_id == paper_id).first()
            if not existing:
                new_survey = LiteratureSurvey(
                    paper_id=paper_id,
                    **validated.model_dump()
                )
                db.add(new_survey)
            else:
                for k, v in validated.model_dump().items():
                    setattr(existing, k, v)
                existing.updated_at = datetime.utcnow()
                
            db.commit()
            
            return {
                "paper_id": paper_id,
                "status": "completed",
                "papers_used": len(analyses),
                "themes_generated": len(validated.themes) if validated.themes else 0
            }
            
        except Exception as e:
            logger.error(f"[LIT_SURVEY] Error generating survey for paper {paper_id}: {e}")
            return {"error": str(e)}
            
    except Exception as e:
        logger.error(f"[LIT_SURVEY] Execution failed: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
