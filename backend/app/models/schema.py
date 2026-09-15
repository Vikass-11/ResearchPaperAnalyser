from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, JSON
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
