from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class LiteratureTheme(BaseModel):
    name: str = Field(..., description="Name of the research theme")
    description: str = Field(..., description="Description of the theme")

class LiteratureSurveyLLMResponse(BaseModel):
    research_context: str
    research_landscape: str
    methodological_comparison: str
    algorithm_model_comparison: str
    findings_synthesis: str
    research_evolution: str
    target_comparison: str
    overall_synthesis: str
    themes_text: List[str]
    similarities: List[str]
    differences: List[str]

class LiteratureSurveySchema(BaseModel):
    research_context: str = Field(..., description="Explanation of domain, topic, and problem context")
    research_landscape: str = Field(..., description="Summary of major research directions")
    themes: List[LiteratureTheme] = Field(..., description="Thematic grouping of papers")
    methodological_comparison: str = Field(..., description="Comparison of methods used across the literature")
    algorithm_model_comparison: str = Field(..., description="Identification of recurring algorithms/models")
    findings_synthesis: str = Field(..., description="Synthesis of recurring findings")
    research_evolution: str = Field(..., description="Evolution of research over time")
    target_comparison: str = Field(..., description="Comparison with the uploaded target research")
    similarities: List[str] = Field(..., description="Similarities between the target and literature")
    differences: List[str] = Field(..., description="Differences between the target and literature")
    overall_synthesis: str = Field(..., description="Overall synthesis and positioning of the target paper")

class LiteratureSurveyResponse(BaseModel):
    id: int
    paper_id: int
    research_context: Optional[str]
    research_landscape: Optional[str]
    themes: Optional[List[LiteratureTheme]]
    methodological_comparison: Optional[str]
    algorithm_model_comparison: Optional[str]
    findings_synthesis: Optional[str]
    research_evolution: Optional[str]
    target_comparison: Optional[str]
    similarities: Optional[List[str]]
    differences: Optional[List[str]]
    overall_synthesis: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
