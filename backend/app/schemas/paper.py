from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class SectionResponse(BaseModel):
    id: int
    section_name: str
    content: str
    
    class Config:
        from_attributes = True

class CitationResponse(BaseModel):
    id: int
    context: str
    section_name: Optional[str] = None
    reference_id: int

    class Config:
        from_attributes = True

class ReferenceResponse(BaseModel):
    id: int
    reference_number: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[List[Any]] = None
    year: Optional[int] = None
    journal_conference: Optional[str] = None
    raw_text: str
    citations: List[CitationResponse] = []
    
    class Config:
        from_attributes = True

class PaperResponse(BaseModel):
    id: int
    title: Optional[str] = None
    authors: Optional[List[Any]] = None
    year: Optional[int] = None
    processing_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PaperDetailResponse(PaperResponse):
    abstract: Optional[str] = None
    summary: Optional[str] = None
    problem_statement: Optional[str] = None
    objective: Optional[str] = None
    methodology: Optional[str] = None
    dataset: Optional[str] = None
    results: Optional[List[Any]] = None
    contributions: Optional[List[Any]] = None
    limitations: Optional[List[Any]] = None
    future_work: Optional[List[Any]] = None
    error_message: Optional[str] = None
    sections: List[SectionResponse] = []
    references: List[ReferenceResponse] = []

class PaperUploadResponse(BaseModel):
    id: int
    status: str
    message: str
