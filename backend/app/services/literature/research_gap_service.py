import os
import json
import logging
import re
from typing import Dict, Any, List
from datetime import datetime

from app.models.database import SessionLocal
from app.models.schema import ResearchProfile, RelatedPaper, LiteratureAnalysis, LiteratureSurvey, ResearchGap
from app.schemas.research_gap import ResearchGapSchema, ResearchGapLLMResponse
from app.services.llm_provider import client, LLM_MODEL
from app.services.literature.research_profile_service import normalize_list_field

logger = logging.getLogger(__name__)

MAX_GAP_ANALYSIS_PAPERS = int(os.getenv("MAX_GAP_ANALYSIS_PAPERS", "10"))
MAX_RESEARCH_GAPS = int(os.getenv("MAX_RESEARCH_GAPS", "10"))

VALID_GAP_TYPES = {
    "Methodological Gap", "Algorithmic Gap", "Model Gap", "Dataset Gap",
    "Evaluation Gap", "Application Gap", "Domain Gap", "Comparative Gap",
    "Scalability Gap", "Generalization Gap", "Reproducibility Gap",
    "Theoretical Gap", "Temporal Gap", "Other"
}

PROMPT_TEMPLATE = """You are an academic research-gap analysis assistant.

Your task is to identify research gaps supported by the supplied research profile, literature survey, and detailed literature analyses.

Use ONLY the supplied evidence.

Do not invent:
- papers
- citations
- datasets
- algorithms
- numerical results
- limitations
- research findings
- future work

A research gap should represent something that appears insufficiently addressed, weakly evaluated, missing, conflicting, outdated, or underexplored in the supplied literature.

Every gap must include evidence explaining why the gap was identified.

Do not produce generic statements such as:
- more research is needed
- future work should investigate this
- AI could improve the field
unless they are directly supported by the supplied evidence.

Return ONLY valid flat JSON matching the requested schema. Do not generate deeply nested objects.
Confidence must be a float between 0.0 and 1.0 representing how strongly the supplied literature supports this gap (NOT model certainty).
You must output a raw valid JSON object, without markdown block formatting. Example:
{{
  "gaps": [
    {{
      "gap_type": "Dataset Gap",
      "title": "Lack of large-scale datasets",
      "description": "...",
      "evidence": ["...", "..."],
      "significance": "...",
      "confidence": 0.8,
      "proposed_direction": "..."
    }}
  ]
}}

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

--- Literature Survey ---
Research Context: {survey_context}
Research Landscape: {survey_landscape}
Themes: {survey_themes}
Methodological Comparison: {survey_methodological}
Algorithm/Model Comparison: {survey_algorithm}
Findings Synthesis: {survey_findings}
Research Evolution: {survey_evolution}
Target Comparison: {survey_target}
Overall Synthesis: {survey_overall}

--- Literature Analysis ---
{literature_context}
"""

RETRY_PROMPT = """Return ONLY valid JSON.
Do not include markdown.
Do not include explanations.
Do not include nested objects.
Return all required fields."""


def normalize_title(title: str) -> str:
    """Normalize string for deduplication."""
    if not title:
        return ""
    # lowercase, strip punctuation, collapse whitespace
    t = title.lower()
    t = re.sub(r'[^\w\s]', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

async def call_llm(prompt: str, retry: bool = False):
    messages = [{"role": "user", "content": prompt}]
    if retry:
        messages.append({"role": "user", "content": RETRY_PROMPT})
        
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=[{
            "type": "function",
            "function": {
                "name": "submit_research_gaps",
                "description": "Submit detected research gaps",
                "parameters": ResearchGapLLMResponse.model_json_schema()
            }
        }],
        tool_choice={"type": "function", "function": {"name": "submit_research_gaps"}},
        temperature=0.3
    )
    
    message = response.choices[0].message
    if message.tool_calls and len(message.tool_calls) > 0:
        return json.loads(message.tool_calls[0].function.arguments)
    elif message.content:
        # Fallback if Llama outputs JSON as text instead of a tool call
        try:
            return json.loads(message.content)
        except json.JSONDecodeError:
            # Try to find JSON block in the text
            import re
            match = re.search(r'\{.*\}', message.content.replace('\n', ''), re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Could not parse JSON from content: {message.content}")
    raise ValueError("LLM returned neither tool_calls nor content.")

async def detect_research_gaps(paper_id: int) -> Dict[str, Any]:
    logger.info(f"[RESEARCH_GAP] Starting Phase 9 for paper {paper_id}")
    
    db = SessionLocal()
    try:
        profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
        if not profile:
            return {"error": "Research profile must be generated before gap detection."}
            
        survey = db.query(LiteratureSurvey).filter(LiteratureSurvey.paper_id == paper_id).first()
        if not survey:
            return {"error": "Literature survey (Phase 8) must be completed before gap detection."}
            
        analyses = (
            db.query(LiteratureAnalysis)
            .join(RelatedPaper, LiteratureAnalysis.related_paper_id == RelatedPaper.id)
            .filter(RelatedPaper.source_paper_id == paper_id)
            .order_by(RelatedPaper.relevance_score.desc())
            .limit(MAX_GAP_ANALYSIS_PAPERS)
            .all()
        )
        
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
        
        survey_themes_str = ", ".join([t.get("name", "") for t in (survey.themes or [])])
        survey_context = {
            "survey_context": survey.research_context or "N/A",
            "survey_landscape": survey.research_landscape or "N/A",
            "survey_themes": survey_themes_str or "N/A",
            "survey_methodological": survey.methodological_comparison or "N/A",
            "survey_algorithm": survey.algorithm_model_comparison or "N/A",
            "survey_findings": survey.findings_synthesis or "N/A",
            "survey_evolution": survey.research_evolution or "N/A",
            "survey_target": survey.target_comparison or "N/A",
            "survey_overall": survey.overall_synthesis or "N/A",
        }
        
        lit_context_strs = []
        paper_lookup = {}
        
        for a in analyses:
            rp = a.related_paper
            paper_lookup[rp.id] = rp.title
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
Models: {a.models}
Key Findings: {a.key_findings}
Limitations: {a.limitations}
Research Direction: {a.research_direction}
Strengths: {a.strengths}
Weaknesses: {a.weaknesses}
Similarities: {a.similarities}
Differences: {a.differences}
Relevance to Target: {a.relevance_to_target}
            """.strip())
            
        literature_context = "\n\n---\n\n".join(lit_context_strs)
        
        prompt = PROMPT_TEMPLATE.format(
            **target_context,
            **survey_context,
            literature_context=literature_context
        )
        
        try:
            try:
                result_json = await call_llm(prompt, retry=False)
            except Exception as e:
                logger.warning(f"[RESEARCH_GAP] LLM call failed, retrying: {e}")
                result_json = await call_llm(prompt, retry=True)
            
            if not result_json or "gaps" not in result_json:
                raise ValueError("Failed to parse gaps from LLM response.")
            
            raw_gaps = result_json.get("gaps", [])
            if isinstance(raw_gaps, str):
                try:
                    raw_gaps = json.loads(raw_gaps)
                except Exception:
                    raw_gaps = []
                    
            processed_gaps = []
            seen_titles = set()
            
            for g in raw_gaps:
                if not isinstance(g, dict):
                    continue
                    
                title = g.get("title", "")
                description = g.get("description", "")
                gap_type = g.get("gap_type", "Other")
                
                # Check for emptiness
                if not title or not description:
                    logger.info(f"Filtered empty title/description: {g}")
                    continue
                    
                # Check confidence
                try:
                    conf = float(g.get("confidence", 0.0))
                except (ValueError, TypeError):
                    conf = 0.5
                if conf < 0.0 or conf > 1.0:
                    logger.info(f"Filtered invalid confidence: {conf}")
                    continue
                
                # Check generic descriptions
                low_desc = description.lower()
                if low_desc == "more research is needed" or "future work should investigate this" in low_desc:
                    logger.info(f"Filtered generic desc: {description}")
                    continue
                    
                # Evidence normalization
                ev = normalize_list_field(g.get("evidence"))
                if not ev:
                    logger.info(f"Filtered empty evidence: {g.get('evidence')}")
                    continue
                
                # Normalize gap type
                if gap_type not in VALID_GAP_TYPES:
                    gap_type = "Other"
                    
                # Deduplication by title
                norm_t = normalize_title(title)
                if not norm_t or norm_t in seen_titles:
                    logger.info(f"Filtered duplicate/empty title: {title}")
                    continue
                seen_titles.add(norm_t)
                
                # Related paper detection from evidence
                related_ids = []
                evidence_text = " ".join(ev).lower()
                for pid, ptitle in paper_lookup.items():
                    if f"paper {pid}" in evidence_text or f"id {pid}" in evidence_text or (ptitle and ptitle.lower() in evidence_text):
                        related_ids.append(pid)
                        
                processed_gaps.append(ResearchGapSchema(
                    gap_type=gap_type,
                    title=title,
                    description=description,
                    evidence=ev,
                    significance=g.get("significance"),
                    related_paper_ids=related_ids,
                    confidence=conf,
                    proposed_direction=g.get("proposed_direction")
                ))
            
            # Sort by confidence and slice to max
            processed_gaps.sort(key=lambda x: x.confidence, reverse=True)
            processed_gaps = processed_gaps[:MAX_RESEARCH_GAPS]
            
            # Idempotent save
            db.query(ResearchGap).filter(ResearchGap.paper_id == paper_id).delete()
            
            for pg in processed_gaps:
                new_gap = ResearchGap(
                    paper_id=paper_id,
                    **pg.model_dump()
                )
                db.add(new_gap)
                
            db.commit()
            
            return {
                "paper_id": paper_id,
                "generated": True,
                "gaps": [pg.model_dump() for pg in processed_gaps]
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"[RESEARCH_GAP] Error parsing LLM response for paper {paper_id}: {e}")
            return {"error": str(e)}
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"[RESEARCH_GAP] Execution failed: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
