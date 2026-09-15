import json
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import List

from app.config import LLM_MODEL, LLM_API_KEY, LLM_BASE_URL

# Initialize AsyncOpenAI client
client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)

class PaperAnalysisOutput(BaseModel):
    summary: str = Field(description="Executive summary of the paper (3-6 paragraphs)")
    problem_statement: str = Field(description="The core problem the paper is solving")
    objective: str = Field(description="The main objective of the research")
    methodology: str = Field(description="Detailed description of the proposed methodology")
    dataset: str = Field(description="Information about datasets used, if any")
    results: List[str] = Field(description="Key findings and results")
    contributions: List[str] = Field(description="Major contributions made by the authors")
    limitations: List[str] = Field(description="Limitations mentioned in the paper")
    future_work: List[str] = Field(description="Future work suggested by the authors")

async def analyze_paper_sections(sections_text: str) -> PaperAnalysisOutput:
    """
    Uses the configured LLM to generate a structured analysis of the paper 
    based on the extracted sections.
    """
    system_prompt = """
    You are an expert academic AI assistant. Your task is to analyze a research paper 
    and extract key information into a structured format. 
    Be factual and ground all your claims in the provided text.
    If a field is not present in the paper, provide an empty list or 'Not mentioned'.
    """
    
    # We truncate if it's absurdly long to fit context windows for the summary step (Groq 8192 token limit)
    user_prompt = f"Here is the text extracted from the paper sections:\n\n{sections_text[:20000]}"
    
    try:
        # Requesting structured output using OpenAI's tool calling API
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            tools=[{
                "type": "function",
                "function": {
                    "name": "submit_paper_analysis",
                    "description": "Submit the structured analysis of the paper.",
                    "parameters": PaperAnalysisOutput.model_json_schema()
                }
            }],
            tool_choice={"type": "function", "function": {"name": "submit_paper_analysis"}},
            temperature=0.2
        )
        
        # Extract arguments from tool call
        tool_call = response.choices[0].message.tool_calls[0]
        result_json = json.loads(tool_call.function.arguments)
        return PaperAnalysisOutput(**result_json)
        
    except Exception as e:
        print(f"LLM analysis failed: {e}")
        # Return fallback
        return PaperAnalysisOutput(
            summary="LLM processing failed or timed out.",
            problem_statement="N/A",
            objective="N/A",
            methodology="N/A",
            dataset="N/A",
            results=[],
            contributions=[],
            limitations=[],
            future_work=[]
        )
