from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class LiteratureAnalysisSchema(BaseModel):
    problem_statement: str = Field(..., description="The research problem the paper addresses.")
    objective: str = Field(..., description="What the paper attempts to achieve.")
    methodology: str = Field(..., description="How the research was conducted.")
    methods: List[str] = Field(default_factory=list, description="Specific methods used.")
    algorithms: List[str] = Field(default_factory=list, description="Algorithms explicitly identified.")
    models: List[str] = Field(default_factory=list, description="Models/frameworks explicitly identified.")
    datasets: List[str] = Field(default_factory=list, description="Dataset or experimental data mentioned.")
    experimental_setup: str = Field(..., description="Experimental or simulation setup described.")
    key_findings: List[str] = Field(default_factory=list, description="Conclusions or results explicitly supported.")
    contributions: List[str] = Field(default_factory=list, description="What the paper contributes.")
    limitations: List[str] = Field(default_factory=list, description="Limitations explicitly stated or supported.")
    research_direction: str = Field(..., description="Direction suggested for future work.")
    strengths: List[str] = Field(default_factory=list, description="Strengths of the paper.")
    weaknesses: List[str] = Field(default_factory=list, description="Weaknesses of the paper.")
    relevance_to_target: str = Field(..., description="Why this paper is relevant to the target research.")
    similarities: List[str] = Field(default_factory=list, description="How it overlaps with the target paper.")
    differences: List[str] = Field(default_factory=list, description="How it differs from the target paper.")

class LiteratureAnalysisResponse(BaseModel):
    id: int
    related_paper_id: int
    problem_statement: Optional[str]
    objective: Optional[str]
    methodology: Optional[str]
    methods: Optional[List[str]]
    algorithms: Optional[List[str]]
    models: Optional[List[str]]
    datasets: Optional[List[str]]
    experimental_setup: Optional[str]
    key_findings: Optional[List[str]]
    contributions: Optional[List[str]]
    limitations: Optional[List[str]]
    research_direction: Optional[str]
    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]
    relevance_to_target: Optional[str]
    similarities: Optional[List[str]]
    differences: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
