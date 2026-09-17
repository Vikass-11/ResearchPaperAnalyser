import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any

from app.config import GROBID_URL

async def process_pdf_with_grobid(file_path: str) -> Dict[str, Any]:
    """
    Sends PDF to GROBID and parses the resulting TEI XML.
    Returns extracted metadata and sections.
    """
    url = f"{GROBID_URL}/api/processFulltextDocument"
    
    try:
        with open(file_path, "rb") as f:
            files = {"input": (file_path, f, "application/pdf")}
            # Long timeout for large PDFs
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, files=files)
                response.raise_for_status()
                
        tei_xml = response.text
        return parse_tei_xml(tei_xml)
    except Exception as e:
        print(f"GROBID processing failed: {e}")
        raise e

def parse_tei_xml(xml_content: str) -> Dict[str, Any]:
    """
    Parses GROBID TEI XML to extract metadata and sections.
    """
    soup = BeautifulSoup(xml_content, "html.parser")
    
    metadata = {
        "title": "",
        "authors": [],
        "abstract": "",
        "year": None
    }
    
    # 1. Title
    title_tag = soup.find("titlestmt")
    if title_tag and title_tag.find("title"):
        metadata["title"] = title_tag.find("title").text.strip()
        
    # 2. Authors
    author_tags = soup.find_all("author")
    for author in author_tags:
        persName = author.find("persname")
        if persName:
            forenames = [f.text for f in persName.find_all("forename")]
            surname = persName.find("surname")
            surname_text = surname.text if surname else ""
            full_name = " ".join(forenames + [surname_text]).strip()
            if full_name:
                metadata["authors"].append(full_name)
                
    # 3. Year
    date_tag = soup.find("date", type="published")
    if date_tag and date_tag.has_attr("when"):
        year_str = date_tag["when"].split("-")[0]
        if year_str.isdigit():
            metadata["year"] = int(year_str)
            
    # 4. Abstract
    abstract_tag = soup.find("abstract")
    if abstract_tag:
        metadata["abstract"] = " ".join([p.text.strip() for p in abstract_tag.find_all("p")])
        
    # 5. Sections and Citations
    sections = []
    citations = []
    body = soup.find("body")
    if body:
        divs = body.find_all("div", recursive=False)
        for div in divs:
            head = div.find("head")
            section_title = head.text.strip() if head else "Unnamed Section"
            
            paragraphs = []
            for p in div.find_all("p"):
                # Extract text for the paragraph
                p_text = p.text.strip()
                paragraphs.append(p_text)
                
                # Extract citations
                for ref in p.find_all("ref", type="bibr"):
                    if ref.has_attr("target") and ref["target"].startswith("#"):
                        target_id = ref["target"][1:] # remove '#'
                        citations.append({
                            "reference_id": target_id,
                            "context": p_text,
                            "section_name": section_title
                        })
            
            content = "\n\n".join(paragraphs)
            if content:
                sections.append({
                    "section_name": section_title,
                    "content": content
                })
                
    # 6. References
    references = []
    list_bibl = soup.find("listbibl")
    if list_bibl:
        for bibl in list_bibl.find_all("biblstruct"):
            ref_id = bibl.get("xml:id", "")
            
            # Title
            title_tag = bibl.find("title", level="a") or bibl.find("title", level="m")
            ref_title = title_tag.text.strip() if title_tag else "Unknown Title"
            
            # Authors
            ref_authors = []
            for author in bibl.find_all("author"):
                persName = author.find("persname")
                if persName:
                    forenames = [f.text for f in persName.find_all("forename")]
                    surname = persName.find("surname")
                    surname_text = surname.text if surname else ""
                    full_name = " ".join(forenames + [surname_text]).strip()
                    if full_name:
                        ref_authors.append(full_name)
                        
            # Year
            ref_year = None
            date_tag = bibl.find("date", type="published")
            if date_tag and date_tag.has_attr("when"):
                year_str = date_tag["when"].split("-")[0]
                if year_str.isdigit():
                    ref_year = int(year_str)
                    
            # Journal/Conference
            journal = None
            monogr_title = bibl.find("title", level="j")
            if monogr_title:
                journal = monogr_title.text.strip()
                
            references.append({
                "id": ref_id,
                "title": ref_title,
                "authors": ref_authors,
                "year": ref_year,
                "journal_conference": journal,
                "raw_text": bibl.text.strip()
            })
                
    return {
        "metadata": metadata,
        "sections": sections,
        "references": references,
        "citations": citations
    }
