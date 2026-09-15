from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class SectionResponse(BaseModel):
    id: int
    section_name: str
    content: str
    
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

class PaperUploadResponse(BaseModel):
    id: int
    status: str
    message: str
