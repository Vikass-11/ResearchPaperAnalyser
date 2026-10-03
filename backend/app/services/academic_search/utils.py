import re
from typing import List
from .models import AcademicPaper
import string

def normalize_title(title: str) -> str:
    if not title:
        return ""
    title = title.lower()
    title = title.translate(str.maketrans('', '', string.punctuation))
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def normalize_doi(doi: str) -> str:
    if not doi:
        return ""
    doi = doi.lower().strip()
    if doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    elif doi.startswith("http://doi.org/"):
        doi = doi.replace("http://doi.org/", "")
    elif doi.startswith("doi:"):
        doi = doi.replace("doi:", "")
    return doi.strip()

def deduplicate_papers(papers: List[AcademicPaper]) -> List[AcademicPaper]:
    seen_dois = set()
    seen_titles = set()
    deduplicated = []
    
    for paper in papers:
        doi = normalize_doi(paper.doi) if paper.doi else None
        title = normalize_title(paper.title) if paper.title else None
        
        is_duplicate = False
        if doi and doi in seen_dois:
            is_duplicate = True
        elif title and title in seen_titles:
            is_duplicate = True
            
        if not is_duplicate:
            deduplicated.append(paper)
            if doi:
                seen_dois.add(doi)
            if title:
                seen_titles.add(title)
                
    return deduplicated
