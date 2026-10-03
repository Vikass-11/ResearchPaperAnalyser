from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, JSON, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=True)
    authors = Column(JSON, nullable=True)  # List of strings or dicts
    abstract = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    keywords = Column(JSON, nullable=True)
    file_path = Column(String, nullable=False)
    
    # Store high-level AI analysis
    summary = Column(Text, nullable=True)
    problem_statement = Column(Text, nullable=True)
    objective = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    dataset = Column(Text, nullable=True)
    results = Column(JSON, nullable=True)
    contributions = Column(JSON, nullable=True)
    limitations = Column(JSON, nullable=True)
    future_work = Column(JSON, nullable=True)
    web_impact_analysis = Column(Text, nullable=True)
    
    processing_status = Column(String, default="UPLOADED") # UPLOADED, PARSING, ANALYZING, COMPLETED, ERROR
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sections = relationship("Section", back_populates="paper", cascade="all, delete-orphan")
    references = relationship("Reference", back_populates="paper", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="paper", cascade="all, delete-orphan")


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    section_name = Column(String, index=True)
    content = Column(Text, nullable=False)
    
    # Evidence tracking
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)

    paper = relationship("Paper", back_populates="sections")


class Reference(Base):
    __tablename__ = "references"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    reference_number = Column(String, nullable=True)  # e.g., "[12]"
    raw_text = Column(Text, nullable=False)
    
    title = Column(String, nullable=True)
    authors = Column(JSON, nullable=True)
    year = Column(Integer, nullable=True)
    journal_conference = Column(String, nullable=True)
    doi = Column(String, nullable=True)
    url = Column(String, nullable=True)
    
    # Verification details (Crossref/OpenAlex)
    verification_status = Column(String, default="UNVERIFIED") # UNVERIFIED, VERIFIED_CROSSREF, VERIFIED_OPENALEX, NOT_FOUND
    citation_count = Column(Integer, nullable=True) # Global citation count from OpenAlex/Crossref
    
    # AI generated analysis for important references
    ai_summary = Column(Text, nullable=True)
    ai_relationship = Column(String, nullable=True) # e.g. "Builds upon", "Compares against"
    ai_contribution = Column(Text, nullable=True)

    paper = relationship("Paper", back_populates="references")
    citations = relationship("Citation", back_populates="reference", cascade="all, delete-orphan")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    reference_id = Column(Integer, ForeignKey("references.id"), nullable=False)
    
    context = Column(Text, nullable=False) # The actual sentence where it is cited
    section_name = Column(String, nullable=True)
    
    # Evidence tracking
    page_number = Column(Integer, nullable=True)
    char_position = Column(Integer, nullable=True) # Offset in the original text
    
    # AI intent classification
    intent = Column(String, nullable=True) # Methodology, Background, Dataset, Comparison, etc.
    why_cited = Column(Text, nullable=True)
    importance_score = Column(Float, nullable=True) # Score based on frequency, context, location

    paper = relationship("Paper", back_populates="citations")
    reference = relationship("Reference", back_populates="citations")

# PaperEmbedding vectors will be stored separately in ChromaDB

class ResearchProfile(Base):
    __tablename__ = "research_profiles"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, unique=True)
    
    research_domain = Column(String, nullable=True)
    sub_domains = Column(JSON, nullable=True)
    research_topic = Column(String, nullable=True)
    research_problem = Column(Text, nullable=True)
    research_objective = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    
    methods = Column(JSON, nullable=True)
    algorithms = Column(JSON, nullable=True)
    models = Column(JSON, nullable=True)
    technologies = Column(JSON, nullable=True)
    datasets = Column(JSON, nullable=True)
    key_concepts = Column(JSON, nullable=True)
    keywords = Column(JSON, nullable=True)
    research_questions = Column(JSON, nullable=True)
    application_domain = Column(String, nullable=True)

    paper = relationship("Paper", backref="research_profile")

class RelatedPaper(Base):
    __tablename__ = "related_papers"

    id = Column(Integer, primary_key=True, index=True)
    source_paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    
    external_id = Column(String, nullable=True, index=True) # e.g. OpenAlex ID
    title = Column(String, nullable=False, index=True)
    authors = Column(JSON, nullable=True)
    abstract = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    doi = Column(String, nullable=True)
    url = Column(String, nullable=True)
    venue = Column(String, nullable=True)
    citation_count = Column(Integer, nullable=True)
    source = Column(String, nullable=True) # OpenAlex, Semantic Scholar, etc.
    paper_type = Column(String, nullable=True)
    keywords = Column(JSON, nullable=True)
    
    relevance_score = Column(Float, nullable=True, index=True)
    category = Column(String, nullable=True) # DISCOVERED
    relationship_type = Column(String, nullable=True) # Directly Related, Methodologically Related
    score_breakdown = Column(JSON, nullable=True)
    is_existing_reference = Column(Boolean, default=False)
    
    # Discovery Metadata
    search_query = Column(String, nullable=True)
    discovery_source = Column(String, nullable=True)
    
    # Analysis fields
    research_problem = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    datasets = Column(Text, nullable=True)
    key_findings = Column(Text, nullable=True)
    limitations = Column(JSON, nullable=True)
    relationship_to_source = Column(Text, nullable=True)
    
    discovered_at = Column(DateTime, default=datetime.utcnow)

    source_paper = relationship("Paper", backref="related_papers")

class LiteratureSurvey(Base):
    __tablename__ = "literature_surveys"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, unique=True)
    
    research_context = Column(Text, nullable=True)
    research_landscape = Column(Text, nullable=True)
    themes = Column(JSON, nullable=True)
    methodological_comparison = Column(Text, nullable=True)
    algorithm_model_comparison = Column(Text, nullable=True)
    findings_synthesis = Column(Text, nullable=True)
    research_evolution = Column(Text, nullable=True)
    target_comparison = Column(Text, nullable=True)
    similarities = Column(JSON, nullable=True)
    differences = Column(JSON, nullable=True)
    overall_synthesis = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    paper = relationship("Paper", backref="literature_survey")

class ResearchGap(Base):
    __tablename__ = "research_gaps"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    
    gap_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)
    significance = Column(Text, nullable=True)
    related_paper_ids = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    proposed_direction = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    paper = relationship("Paper", backref="identified_gaps")

class LiteratureAnalysis(Base):
    __tablename__ = "literature_analyses"

    id = Column(Integer, primary_key=True, index=True)
    related_paper_id = Column(Integer, ForeignKey("related_papers.id"), nullable=False, unique=True, index=True)
    
    problem_statement = Column(Text, nullable=True)
    objective = Column(Text, nullable=True)
    methodology = Column(Text, nullable=True)
    methods = Column(JSON, nullable=True)
    algorithms = Column(JSON, nullable=True)
    models = Column(JSON, nullable=True)
    datasets = Column(JSON, nullable=True)
    experimental_setup = Column(Text, nullable=True)
    key_findings = Column(JSON, nullable=True)
    contributions = Column(JSON, nullable=True)
    limitations = Column(JSON, nullable=True)
    research_direction = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    relevance_to_target = Column(Text, nullable=True)
    similarities = Column(JSON, nullable=True)
    differences = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    related_paper = relationship("RelatedPaper", backref="analysis")

class RecentResearch(Base):
    __tablename__ = "recent_research"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False, index=True)
    
    external_id = Column(String, nullable=True)
    source = Column(String, nullable=True)
    title = Column(String, nullable=False)
    authors = Column(JSON, nullable=True)
    abstract = Column(Text, nullable=True)
    year = Column(Integer, nullable=False, index=True)
    doi = Column(String, nullable=True)
    url = Column(String, nullable=True)
    venue = Column(String, nullable=True)
    citation_count = Column(Integer, nullable=True)
    
    relevance_score = Column(Float, nullable=False, index=True)
    relevance_reason = Column(Text, nullable=True)
    relationship_type = Column(String, nullable=False)
    
    is_newer_than_target = Column(Boolean, default=False)
    addresses_gap = Column(Boolean, default=False)
    related_gap_ids = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    paper = relationship("Paper", backref="recent_research")
