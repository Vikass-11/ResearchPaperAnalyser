import json
import logging
from typing import Optional
from app.models.database import SessionLocal
from app.models.schema import Paper, ResearchProfile
from app.services.llm_provider import client
from app.config import LLM_MODEL
from app.schemas.literature import ResearchProfileSchema

logger = logging.getLogger(__name__)

def normalize_list_field(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value == "" or value == "[]" or value.lower() == "null":
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return [item.strip() for item in value.split(',') if item.strip()]
    return []

async def generate_research_profile(paper_id: int) -> Optional[ResearchProfileSchema]:
    logger.info(f"[RESEARCH_PROFILE] Starting profile extraction for paper {paper_id}")
    
    db = SessionLocal()
    try:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            logger.error(f"[RESEARCH_PROFILE] Paper {paper_id} not found")
            return None
            
        # Build LLM input context
        context_parts = []
        if paper.title: context_parts.append(f"Title: {paper.title}")
        if paper.authors: context_parts.append(f"Authors: {', '.join(paper.authors)}")
        if paper.abstract: context_parts.append(f"Abstract: {paper.abstract}")
        if paper.problem_statement: context_parts.append(f"Problem Statement: {paper.problem_statement}")
        if paper.objective: context_parts.append(f"Objective: {paper.objective}")
        if paper.methodology: context_parts.append(f"Methodology: {paper.methodology}")
        if paper.contributions: context_parts.append(f"Contributions: {json.dumps(paper.contributions)}")
        
        # Add limited sections prioritizing Intro, Methods, Results, Conclusion
        sections_added = 0
        for section in paper.sections:
            name_lower = section.section_name.lower()
            if any(k in name_lower for k in ['intro', 'method', 'result', 'conclu']):
                context_parts.append(f"Section - {section.section_name}:\n{section.content[:1500]}")
                sections_added += 1
            if sections_added >= 4:
                break
                
        context = "\n\n".join(context_parts)
        
        system_prompt = """
        You are an expert academic research analyst. Your job is to identify what this paper is actually researching and generate a structured Research Profile.
        
        Rules:
        - Do not invent keywords, datasets, algorithms, technologies, or research questions.
        - Only extract what is supported by the text.
        - If information is unavailable, use "Not explicitly stated" for strings, or an empty list [] for arrays.
        - Do not hallucinate.
        - Determine the true academic domain from the research content, not just affiliations.
        - Generate 8-15 high-value academic search keywords.
        """
        
        user_prompt = f"Extract the research profile for the following paper:\n\n{context[:15000]}"
        
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "submit_research_profile",
                    "description": "Submit the extracted research profile",
                    "parameters": ResearchProfileSchema.model_json_schema()
                }
            }],
            tool_choice={"type": "function", "function": {"name": "submit_research_profile"}},
            temperature=0.2
        )
        
        tool_call = response.choices[0].message.tool_calls[0]
        result_json = json.loads(tool_call.function.arguments)
        
        # Normalize list fields
        list_fields = [
            "sub_domains", "methods", "algorithms", "models", 
            "technologies", "datasets", "key_concepts", 
            "keywords", "research_questions"
        ]
        for field in list_fields:
            if field in result_json:
                result_json[field] = normalize_list_field(result_json.get(field))
        
        # Validate with Pydantic
        profile_data = ResearchProfileSchema(**result_json)
        
        logger.info(f"[RESEARCH_PROFILE] Paper topic detected: {profile_data.research_topic}")
        logger.info(f"[RESEARCH_PROFILE] Generated {len(profile_data.keywords)} keywords")
        
        # Save to DB
        db_profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
        if not db_profile:
            db_profile = ResearchProfile(paper_id=paper_id)
            db.add(db_profile)
            
        # Update fields
        for key, value in profile_data.model_dump().items():
            setattr(db_profile, key, value)
            
        db.commit()
        logger.info(f"[RESEARCH_PROFILE] Profile saved successfully for paper {paper_id}")
        
        return profile_data
        
    except Exception as e:
        logger.error(f"[RESEARCH_PROFILE] Generation failed for paper {paper_id}: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()
