from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class PaperResponse(BaseModel):
    id: int
    title: Optional[str] = None
    authors: Optional[List[Any]] = None
    year: Optional[int] = None
    processing_status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PaperUploadResponse(BaseModel):
    id: int
    status: str
    message: str
