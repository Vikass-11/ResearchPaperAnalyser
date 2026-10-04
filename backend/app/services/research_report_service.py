from datetime import datetime, timezone
import os
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.schema import Paper, ResearchProfile, RelatedPaper, LiteratureAnalysis, LiteratureSurvey, ResearchGap, RecentResearch
from app.schemas.research_report import (
    ResearchReportSchema, ResearchReportMetadata, ExportLimits,
    ResearchReportPaperSection, ResearchProfileExport, LiteratureSurveyExport,
    LiteratureSectionExport, RelatedPaperExport, ResearchGapsExport, RecentResearchExport
)
from app.schemas.literature_analysis import LiteratureAnalysisResponse
from app.schemas.literature_survey import LiteratureSurveyResponse
from app.schemas.research_gap import ResearchGapSchema
from app.schemas.recent_research import RecentResearchSchema

EXPORT_MAX_RELATED_PAPERS = int(os.getenv("EXPORT_MAX_RELATED_PAPERS", "50"))
EXPORT_MAX_ANALYSES = int(os.getenv("EXPORT_MAX_ANALYSES", "20"))
EXPORT_MAX_RECENT_RESEARCH = int(os.getenv("EXPORT_MAX_RECENT_RESEARCH", "50"))
EXPORT_MAX_RESEARCH_GAPS = int(os.getenv("EXPORT_MAX_RESEARCH_GAPS", "20"))

def build_research_report(paper_id: int, db: Session) -> ResearchReportSchema:
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise ValueError("Paper not found")
        
    profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper_id).first()
    
    # Base Paper Section
    paper_section = ResearchReportPaperSection(
        id=paper.id,
        title=paper.title,
        authors=paper.authors,
        abstract=paper.abstract,
        year=paper.year,
        keywords=paper.keywords
    )
    
    # Profile
    profile_export = ResearchProfileExport(
        available=profile is not None,
        data={
            "research_domain": profile.research_domain,
            "sub_domains": profile.sub_domains,
            "research_topic": profile.research_topic,
            "research_problem": profile.research_problem,
            "research_objective": profile.research_objective,
            "methodology": profile.methodology,
            "methods": profile.methods,
            "algorithms": profile.algorithms,
            "models": profile.models,
            "technologies": profile.technologies,
            "datasets": profile.datasets,
            "key_concepts": profile.key_concepts,
            "keywords": profile.keywords,
            "research_questions": profile.research_questions,
            "application_domain": profile.application_domain
        } if profile else None
    )
    
    # Related Papers
    related_query = db.query(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id).order_by(RelatedPaper.citation_count.desc().nullslast())
    related_count = related_query.count()
    related_papers = related_query.limit(EXPORT_MAX_RELATED_PAPERS).all()
    
    ranked_query = db.query(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id).filter(RelatedPaper.relevance_score.isnot(None)).order_by(RelatedPaper.relevance_score.desc())
    ranked_papers = ranked_query.limit(EXPORT_MAX_RELATED_PAPERS).all()
    
    analyses_query = db.query(LiteratureAnalysis).join(RelatedPaper).filter(RelatedPaper.source_paper_id == paper_id)
    analyses_count = analyses_query.count()
    analyses = analyses_query.limit(EXPORT_MAX_ANALYSES).all()
    
    literature_section = LiteratureSectionExport(
        available=related_count > 0,
        related_papers=[
            RelatedPaperExport(
                id=p.id, title=p.title or "Unknown Title", authors=p.authors, year=p.year,
                venue=p.venue, relationship_type=p.relationship_type, relevance_score=p.relevance_score, source=p.source
            ) for p in related_papers
        ],
        ranked_papers=[
            RelatedPaperExport(
                id=p.id, title=p.title or "Unknown Title", authors=p.authors, year=p.year,
                venue=p.venue, relationship_type=p.relationship_type, relevance_score=p.relevance_score, source=p.source
            ) for p in ranked_papers
        ],
        analyses=[LiteratureAnalysisResponse.model_validate(a) for a in analyses]
    )
    
    # Survey
    survey = db.query(LiteratureSurvey).filter(LiteratureSurvey.paper_id == paper_id).first()
    survey_export = LiteratureSurveyExport(
        available=survey is not None,
        data=LiteratureSurveyResponse.model_validate(survey) if survey else None
    )
    
    # Gaps
    gaps_query = db.query(ResearchGap).filter(ResearchGap.paper_id == paper_id).order_by(ResearchGap.confidence.desc())
    gaps_count = gaps_query.count()
    gaps = gaps_query.limit(EXPORT_MAX_RESEARCH_GAPS).all()
    
    gaps_schema_list = []
    for g in gaps:
        evidence_list = g.evidence if isinstance(g.evidence, list) else ([g.evidence] if g.evidence else [])
        related_ids = g.related_paper_ids if isinstance(g.related_paper_ids, list) else []
        gaps_schema_list.append(ResearchGapSchema(
            gap_type=g.gap_type,
            title=g.title,
            description=g.description,
            evidence=evidence_list,
            significance=g.significance,
            related_paper_ids=related_ids,
            confidence=g.confidence,
            proposed_direction=g.proposed_direction
        ))
        
    gaps_export = ResearchGapsExport(
        available=gaps_count > 0,
        gaps=gaps_schema_list
    )
    
    # Recent Research
    recent_query = db.query(RecentResearch).filter(RecentResearch.paper_id == paper_id).order_by(RecentResearch.relevance_score.desc())
    recent_count = recent_query.count()
    recent = recent_query.limit(EXPORT_MAX_RECENT_RESEARCH).all()
    
    recent_schema_list = []
    for r in recent:
        recent_schema_list.append(RecentResearchSchema(
            id=r.id,
            paper_id=r.paper_id,
            external_id=r.external_id,
            source=r.source,
            title=r.title,
            abstract=r.abstract,
            year=r.year,
            doi=r.doi,
            url=r.url,
            venue=r.venue,
            citation_count=r.citation_count,
            relevance_score=r.relevance_score,
            relevance_reason=r.relevance_reason,
            relationship_type=r.relationship_type,
            is_newer_than_target=r.is_newer_than_target,
            addresses_gap=r.addresses_gap,
            related_gap_ids=r.related_gap_ids if isinstance(r.related_gap_ids, list) else [],
            created_at=r.created_at,
            updated_at=r.updated_at
        ))
        
    recent_export = RecentResearchExport(
        available=recent_count > 0,
        recent=recent_schema_list
    )
    
    # Limits & Metadata
    limits = ExportLimits(
        related_papers_limit=EXPORT_MAX_RELATED_PAPERS,
        related_papers_truncated=related_count > EXPORT_MAX_RELATED_PAPERS,
        analyses_limit=EXPORT_MAX_ANALYSES,
        analyses_truncated=analyses_count > EXPORT_MAX_ANALYSES,
        recent_research_limit=EXPORT_MAX_RECENT_RESEARCH,
        recent_research_truncated=recent_count > EXPORT_MAX_RECENT_RESEARCH,
        research_gaps_limit=EXPORT_MAX_RESEARCH_GAPS,
        research_gaps_truncated=gaps_count > EXPORT_MAX_RESEARCH_GAPS
    )
    
    metadata = ResearchReportMetadata(
        report_version="1.0",
        generated_at=datetime.now(timezone.utc).isoformat(),
        paper_id=paper_id,
        export_limits=limits
    )
    
    report = ResearchReportSchema(
        metadata=metadata,
        paper=paper_section,
        research_profile=profile_export,
        literature=literature_section,
        literature_survey=survey_export,
        research_gaps=gaps_export,
        recent_research=recent_export
    )
    return report

def generate_markdown_report(report: ResearchReportSchema) -> str:
    md = [f"# Research Analysis Report"]
    
    md.append(f"Generated At: {report.metadata.generated_at}\nReport Version: {report.metadata.report_version}\n")
    
    # 1. Paper Information
    md.append("## 1. Paper Information\n")
    md.append(f"- **Title**: {report.paper.title}")
    md.append(f"- **Authors**: {', '.join(report.paper.authors) if report.paper.authors else 'Unknown'}")
    md.append(f"- **Year**: {report.paper.year}")
    
    # 2. Research Profile
    md.append("\n## 2. Research Profile\n")
    if report.research_profile.available and report.research_profile.data:
        data = report.research_profile.data
        for k, v in data.items():
            formatted_key = k.replace('_', ' ').title()
            if isinstance(v, list):
                md.append(f"### {formatted_key}\n")
                if v:
                    for item in v:
                        md.append(f"- {item}")
                else:
                    md.append("None")
                md.append("")
            else:
                md.append(f"### {formatted_key}\n{v}\n")
    else:
        md.append("Research profile is not available.\n")
        
    # 3. Related Literature
    md.append("## 3. Related Literature\n")
    if report.literature.available and report.literature.ranked_papers:
        md.append("| Paper | Year | Relationship | Relevance |")
        md.append("|---|---:|---|---:|")
        for p in report.literature.ranked_papers:
            score = f"{p.relevance_score:.3f}" if p.relevance_score else "N/A"
            md.append(f"| {p.title} | {p.year or 'N/A'} | {p.relationship_type or 'N/A'} | {score} |")
        md.append("")
    else:
        md.append("Related literature is not available.\n")
        
    # 4. Detailed Literature Analysis
    md.append("## 4. Detailed Literature Analysis\n")
    if report.literature.analyses:
        for a in report.literature.analyses:
            # We must look up the title from the related_papers array in the report!
            related_title = "Unknown Title"
            for rp in report.literature.related_papers + report.literature.ranked_papers:
                if rp.id == a.related_paper_id:
                    related_title = rp.title
                    break
                    
            md.append(f"### {related_title}")
            md.append(f"- **Problem**: {a.problem_statement}")
            md.append(f"- **Objective**: {a.objective}")
            md.append(f"- **Methodology**: {a.methodology}")
            md.append(f"- **Methods**: {', '.join(a.methods) if a.methods else 'N/A'}")
            md.append(f"- **Algorithms**: {', '.join(a.algorithms) if a.algorithms else 'N/A'}")
            md.append(f"- **Models**: {', '.join(a.models) if a.models else 'N/A'}")
            key_findings_str = ', '.join(a.key_findings) if isinstance(a.key_findings, list) else a.key_findings
            md.append(f"- **Key Findings**: {key_findings_str if key_findings_str else 'N/A'}")
            contributions_str = ', '.join(a.contributions) if isinstance(a.contributions, list) else a.contributions
            md.append(f"- **Contributions**: {contributions_str if contributions_str else 'N/A'}")
            md.append(f"- **Limitations**: {', '.join(a.limitations) if a.limitations else 'N/A'}")
            md.append(f"- **Research Direction**: {a.research_direction}")
            md.append(f"- **Strengths**: {', '.join(a.strengths) if a.strengths else 'N/A'}")
            md.append(f"- **Weaknesses**: {', '.join(a.weaknesses) if a.weaknesses else 'N/A'}")
            md.append(f"- **Similarities**: {', '.join(a.similarities) if a.similarities else 'N/A'}")
            md.append(f"- **Differences**: {', '.join(a.differences) if a.differences else 'N/A'}")
            md.append(f"- **Relevance to Target**: {a.relevance_to_target}\n")
    else:
        md.append("Detailed literature analyses are not available.\n")
        
    # 5. Literature Survey
    md.append("## 5. Literature Survey\n")
    if report.literature_survey.available and report.literature_survey.data:
        s = report.literature_survey.data
        md.append(f"### Research Context\n{s.research_context}\n")
        md.append(f"### Research Landscape\n{s.research_landscape}\n")
        
        md.append("### Themes\n")
        if s.themes:
            for t in s.themes:
                md.append(f"**{t.name}**")
                md.append(f"- *Description*: {t.description}\n")
                
        md.append(f"### Methodological Comparison\n{s.methodological_comparison}\n")
        md.append(f"### Algorithm/Model Comparison\n{s.algorithm_model_comparison}\n")
        md.append(f"### Findings Synthesis\n{s.findings_synthesis}\n")
        md.append(f"### Research Evolution\n{s.research_evolution}\n")
        md.append(f"### Target Comparison\n{s.target_comparison}\n")
        
        md.append("### Similarities\n")
        if s.similarities:
            for sim in s.similarities:
                md.append(f"- {sim}")
        md.append("")
        
        md.append("### Differences\n")
        if s.differences:
            for diff in s.differences:
                md.append(f"- {diff}")
        md.append("")
        
        md.append(f"### Overall Synthesis\n{s.overall_synthesis}\n")
    else:
        md.append("Literature survey is not available.\n")
        
    # 6. Research Gaps
    md.append("## 6. Research Gaps\n")
    if report.research_gaps.available and report.research_gaps.gaps:
        for g in report.research_gaps.gaps:
            md.append(f"### {g.title}")
            md.append(f"- **Type**: {g.gap_type}")
            md.append(f"- **Description**: {g.description}")
            md.append(f"- **Evidence**: {g.evidence}")
            md.append(f"- **Significance**: {g.significance}")
            md.append(f"- **Confidence**: {g.confidence}")
            md.append(f"- **Proposed Direction**: {g.proposed_direction}")
            md.append(f"- **Supporting Papers**: {', '.join(str(p) for p in g.related_paper_ids) if g.related_paper_ids else 'N/A'}\n")
    else:
        md.append("Research gaps are not available.\n")
        
    # 7. Recent Research
    md.append("## 7. Recent Research\n")
    if report.recent_research.available and report.recent_research.recent:
        md.append("| Paper | Year | Source | Relevance | Relationship | Addresses Gap |")
        md.append("|---|---:|---|---:|---|---|")
        for r in report.recent_research.recent:
            score = f"{r.relevance_score:.3f}" if r.relevance_score else "N/A"
            md.append(f"| {r.title} | {r.year or 'N/A'} | {r.source or 'N/A'} | {score} | {r.relationship_type or 'N/A'} | {r.addresses_gap} |")
        md.append("")
    else:
        md.append("Recent research is not available.\n")
        
    # 8. Overall Research Landscape
    md.append("## 8. Overall Research Landscape\n")
    counts = []
    if report.literature.available:
        counts.append(f"{len(report.literature.related_papers)} related papers found")
    if report.literature_survey.available:
        counts.append("literature synthesized")
    if report.research_gaps.available:
        counts.append(f"{len(report.research_gaps.gaps)} research gaps identified")
    if report.recent_research.available:
        counts.append(f"{len(report.recent_research.recent)} recent research papers analyzed")
        
    if counts:
        md.append(f"This report presents an automated analysis of the target paper's position within the academic landscape, integrating {', '.join(counts)}.\n")
    else:
        md.append("No significant research data is available for this paper.\n")

    return "\n".join(md)

import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

def generate_pdf_report(report: ResearchReportSchema) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=36, leftMargin=36,
        topMargin=36, bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontName='Helvetica', fontSize=10, leading=12))
    styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=18, spaceAfter=20))
    styles.add(ParagraphStyle(name='Heading1Custom', fontName='Helvetica-Bold', fontSize=16, spaceBefore=15, spaceAfter=10))
    styles.add(ParagraphStyle(name='Heading2Custom', fontName='Helvetica-Bold', fontSize=14, spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle(name='Heading3Custom', fontName='Helvetica-Bold', fontSize=12, spaceBefore=10, spaceAfter=6))
    
    normal = styles['Normal']
    justify = styles['Justify']
    
    elements = []
    
    # Title
    elements.append(Paragraph("Research Analysis Report", styles['CenterTitle']))
    elements.append(Paragraph(f"Generated At: {report.metadata.generated_at}", normal))
    elements.append(Paragraph(f"Report Version: {report.metadata.report_version}", normal))
    elements.append(Spacer(1, 20))
    
    # 1. Paper Info
    elements.append(Paragraph("1. Paper Information", styles['Heading1Custom']))
    title = report.paper.title or "Unknown"
    authors = ", ".join(report.paper.authors) if report.paper.authors else "Unknown"
    year = str(report.paper.year) if report.paper.year else "Unknown"
    
    elements.append(Paragraph(f"<b>Title:</b> {title}", normal))
    elements.append(Paragraph(f"<b>Authors:</b> {authors}", normal))
    elements.append(Paragraph(f"<b>Year:</b> {year}", normal))
    elements.append(Spacer(1, 10))
    
    # 2. Research Profile
    elements.append(Paragraph("2. Research Profile", styles['Heading1Custom']))
    if report.research_profile.available and report.research_profile.data:
        data = report.research_profile.data
        for k, v in data.items():
            formatted_key = k.replace('_', ' ').title()
            elements.append(Paragraph(formatted_key, styles['Heading2Custom']))
            if isinstance(v, list):
                if v:
                    for item in v:
                        elements.append(Paragraph(f"- {item}", normal))
                else:
                    elements.append(Paragraph("None", normal))
            else:
                elements.append(Paragraph(str(v), justify))
            elements.append(Spacer(1, 5))
    else:
        elements.append(Paragraph("Research profile is not available.", normal))
        
    elements.append(PageBreak())
        
    # 3. Related Literature
    elements.append(Paragraph("3. Related Literature", styles['Heading1Custom']))
    if report.literature.available and report.literature.ranked_papers:
        data = [["Paper Title", "Year", "Relationship", "Score"]]
        for p in report.literature.ranked_papers[:30]: # Limit table size in PDF to prevent infinite loop errors
            title = (p.title[:60] + '...') if p.title and len(p.title) > 60 else (p.title or 'Unknown')
            year = str(p.year) if p.year else 'N/A'
            rel = p.relationship_type or 'N/A'
            score = f"{p.relevance_score:.3f}" if p.relevance_score else 'N/A'
            data.append([title, year, rel, score])
            
        t = Table(data, colWidths=[250, 40, 150, 50], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("Related literature is not available.", normal))
        
    elements.append(PageBreak())
    
    # 4. Detailed Literature Analysis
    elements.append(Paragraph("4. Detailed Literature Analysis", styles['Heading1Custom']))
    if report.literature.analyses:
        for a in report.literature.analyses:
            related_title = "Unknown Title"
            for rp in report.literature.related_papers + report.literature.ranked_papers:
                if rp.id == a.related_paper_id:
                    related_title = rp.title
                    break
            elements.append(Paragraph(related_title, styles['Heading2Custom']))
            elements.append(Paragraph(f"<b>Problem:</b> {a.problem_statement}", normal))
            elements.append(Paragraph(f"<b>Objective:</b> {a.objective}", normal))
            elements.append(Paragraph(f"<b>Methodology:</b> {a.methodology}", normal))
            key_findings_str = ', '.join(a.key_findings) if isinstance(a.key_findings, list) else a.key_findings
            elements.append(Paragraph(f"<b>Key Findings:</b> {key_findings_str}", normal))
            elements.append(Paragraph(f"<b>Relevance to Target:</b> {a.relevance_to_target}", justify))
            elements.append(Spacer(1, 10))
    else:
        elements.append(Paragraph("Detailed literature analyses are not available.", normal))
        
    # 5. Literature Survey
    elements.append(Paragraph("5. Literature Survey", styles['Heading1Custom']))
    if report.literature_survey.available and report.literature_survey.data:
        s = report.literature_survey.data
        elements.append(Paragraph("Research Context", styles['Heading2Custom']))
        elements.append(Paragraph(s.research_context, justify))
        elements.append(Paragraph("Research Landscape", styles['Heading2Custom']))
        elements.append(Paragraph(s.research_landscape, justify))
        elements.append(Paragraph("Methodological Comparison", styles['Heading2Custom']))
        elements.append(Paragraph(s.methodological_comparison, justify))
        elements.append(Paragraph("Findings Synthesis", styles['Heading2Custom']))
        elements.append(Paragraph(s.findings_synthesis, justify))
        elements.append(Paragraph("Overall Synthesis", styles['Heading2Custom']))
        elements.append(Paragraph(s.overall_synthesis, justify))
    else:
        elements.append(Paragraph("Literature survey is not available.", normal))
        
    elements.append(PageBreak())
        
    # 6. Research Gaps
    elements.append(Paragraph("6. Research Gaps", styles['Heading1Custom']))
    if report.research_gaps.available and report.research_gaps.gaps:
        for g in report.research_gaps.gaps:
            elements.append(Paragraph(g.title, styles['Heading2Custom']))
            elements.append(Paragraph(f"<b>Type:</b> {g.gap_type}", normal))
            elements.append(Paragraph(f"<b>Description:</b> {g.description}", justify))
            elements.append(Paragraph(f"<b>Evidence:</b> {g.evidence}", justify))
            elements.append(Paragraph(f"<b>Proposed Direction:</b> {g.proposed_direction}", justify))
            elements.append(Spacer(1, 10))
    else:
        elements.append(Paragraph("Research gaps are not available.", normal))
        
    # 7. Recent Research
    elements.append(Paragraph("7. Recent Research", styles['Heading1Custom']))
    if report.recent_research.available and report.recent_research.recent:
        data = [["Title", "Year", "Relationship", "Addresses Gap"]]
        for r in report.recent_research.recent[:30]:
            title = (r.title[:60] + '...') if r.title and len(r.title) > 60 else (r.title or 'Unknown')
            year = str(r.year) if r.year else 'N/A'
            rel = r.relationship_type or 'N/A'
            gap = str(r.addresses_gap)
            data.append([title, year, rel, gap])
            
        t = Table(data, colWidths=[250, 40, 150, 50], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.lightgreen),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP')
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("Recent research is not available.", normal))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
