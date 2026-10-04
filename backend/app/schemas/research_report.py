from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from app.schemas.paper import PaperResponse
from app.schemas.literature_analysis import LiteratureAnalysisResponse
from app.schemas.literature_survey import LiteratureSurveyResponse
from app.schemas.research_gap import ResearchGapSchema
from app.schemas.recent_research import RecentResearchSchema

class ExportLimits(BaseModel):
    related_papers_limit: int
    related_papers_truncated: bool
    analyses_limit: int
    analyses_truncated: bool
    recent_research_limit: int
    recent_research_truncated: bool
    research_gaps_limit: int
    research_gaps_truncated: bool

class ResearchReportMetadata(BaseModel):
    report_version: str = "1.0"
    generated_at: str
    paper_id: int
    export_limits: ExportLimits

class ResearchReportPaperSection(BaseModel):
    id: int
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    year: Optional[int] = None
    keywords: Optional[List[str]] = None

class ResearchProfileExport(BaseModel):
    available: bool
    data: Optional[Dict[str, Any]] = None

class LiteratureSurveyExport(BaseModel):
    available: bool
    data: Optional[LiteratureSurveyResponse] = None

class RelatedPaperExport(BaseModel):
    id: int
    title: str
    authors: Optional[List[str]] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    relationship_type: Optional[str] = None
    relevance_score: Optional[float] = None
    source: Optional[str] = None

class LiteratureSectionExport(BaseModel):
    available: bool
    related_papers: List[RelatedPaperExport] = []
    ranked_papers: List[RelatedPaperExport] = []
    analyses: List[LiteratureAnalysisResponse] = []

class ResearchGapsExport(BaseModel):
    available: bool
    gaps: List[ResearchGapSchema] = []

class RecentResearchExport(BaseModel):
    available: bool
    recent: List[RecentResearchSchema] = []

class ResearchReportSchema(BaseModel):
    metadata: ResearchReportMetadata
    paper: ResearchReportPaperSection
    research_profile: ResearchProfileExport
    literature: LiteratureSectionExport
    literature_survey: LiteratureSurveyExport
    research_gaps: ResearchGapsExport
    recent_research: RecentResearchExport

    model_config = ConfigDict(from_attributes=True)
