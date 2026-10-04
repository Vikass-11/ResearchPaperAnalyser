import pytest
import asyncio
from app.services.academic_search.models import AcademicPaper
from app.services.academic_search.utils import deduplicate_papers, normalize_title, normalize_doi

def test_normalize_title():
    assert normalize_title("Deep Learning for Medical Image Analysis") == "deep learning for medical image analysis"
    assert normalize_title("Deep Learning for Medical Image Analysis.") == "deep learning for medical image analysis"
    assert normalize_title("Deep  Learning, for Medical Image Analysis!") == "deep learning for medical image analysis"
    
def test_normalize_doi():
    assert normalize_doi("https://doi.org/10.123/456") == "10.123/456"
    assert normalize_doi("doi:10.123/456") == "10.123/456"
    assert normalize_doi("  10.123/456  ") == "10.123/456"
    
def test_deduplicate_papers():
    papers = [
        AcademicPaper(source="OpenAlex", title="Deep Learning for Medical Image Analysis", doi="10.123/456"),
        AcademicPaper(source="Semantic Scholar", title="Deep Learning for Medical Image Analysis.", doi="10.123/456"),
        AcademicPaper(source="Crossref", title="A completely different paper", doi="10.999/888"),
        AcademicPaper(source="OpenAlex", title="A completely different paper", doi=None),
    ]
    
    deduped = deduplicate_papers(papers)
    assert len(deduped) == 2
    assert deduped[0].title == "Deep Learning for Medical Image Analysis"
    assert deduped[1].title == "A completely different paper"
