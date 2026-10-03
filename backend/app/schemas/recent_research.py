from pydantic import BaseModel, Field
from typing import List, Optional

class RecentResearchSchema(BaseModel):
    external_id: Optional[str] = None
    source: Optional[str] = None
    title: str = Field(...)
    authors: List[str] = Field(default_factory=list)
    abstract: Optional[str] = None
    year: int = Field(..., gt=1900)
    doi: Optional[str] = None
    url: Optional[str] = None
    venue: Optional[str] = None
    citation_count: Optional[int] = None
    
    relevance_score: float = Field(..., ge=0.0)
    relevance_reason: Optional[str] = None
    relationship_type: str = Field(...)
    
    is_newer_than_target: bool = Field(default=False)
    addresses_gap: bool = Field(default=False)
    related_gap_ids: List[int] = Field(default_factory=list)
