from pydantic import BaseModel
from typing import List, Optional, Any

class AcademicPaper(BaseModel):
    external_id: Optional[str] = None
    source: str
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    venue: Optional[str] = None
    citation_count: int = 0
    paper_type: Optional[str] = None
    keywords: List[str] = []
    raw_metadata: Any = None
