import json
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import List

from app.config import LLM_MODEL, LLM_API_KEY, LLM_BASE_URL, LLM_TIMEOUT_SECONDS, LLM_MAX_RETRIES

# Initialize AsyncOpenAI client
client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
    timeout=LLM_TIMEOUT_SECONDS,
    max_retries=LLM_MAX_RETRIES
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

async def synthesize_web_impact(title: str, search_results: List[dict]) -> str:
    """
    Synthesizes web search results into a comprehensive summary of the paper's impact and reception.
    """
    if not search_results:
        return "No significant web impact or discussions found."

    system_prompt = "You are an expert academic research assistant. Synthesize the web search results to describe the real-world impact, reception, and discussions surrounding the paper."
    
    context = ""
    for idx, res in enumerate(search_results):
        context += f"\nResult {idx+1}:\nTitle: {res.get('title')}\nSnippet: {res.get('body')}\nURL: {res.get('href')}\n"

    user_prompt = f"Paper Title: {title}\n\nWeb Search Results:{context}\n\nPlease provide a 1-3 paragraph summary focusing on the paper's reception in the community, its practical impact, any notable implementations, and general discussions. Use markdown."
    
    try:
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM web impact synthesis failed: {e}")
        return "Failed to synthesize web impact."
