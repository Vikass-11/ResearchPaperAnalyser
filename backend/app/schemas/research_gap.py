from pydantic import BaseModel, Field
from typing import List, Optional

class ResearchGapLLMItem(BaseModel):
    gap_type: str
    title: str
    description: str
    evidence: List[str]
    significance: str
    confidence: float
    proposed_direction: str

class ResearchGapLLMResponse(BaseModel):
    gaps: List[ResearchGapLLMItem]

class ResearchGapSchema(BaseModel):
    gap_type: str = Field(..., description="Category of the research gap")
    title: str = Field(..., description="Short title of the gap")
    description: str = Field(..., description="Detailed description of the gap")
    evidence: List[str] = Field(default_factory=list, description="Evidence supporting this gap")
    significance: Optional[str] = Field(None, description="Significance of addressing this gap")
    related_paper_ids: List[int] = Field(default_factory=list, description="List of related paper IDs that support this gap")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    proposed_direction: Optional[str] = Field(None, description="Proposed research direction")
