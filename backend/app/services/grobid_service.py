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
        
    # 5. Sections
    sections = []
    body = soup.find("body")
    if body:
        divs = body.find_all("div", recursive=False)
        for div in divs:
            head = div.find("head")
            section_title = head.text.strip() if head else "Unnamed Section"
            
            paragraphs = []
            for p in div.find_all("p"):
                paragraphs.append(p.text.strip())
            
            content = "\n\n".join(paragraphs)
            if content:
                sections.append({
                    "section_name": section_title,
                    "content": content
                })
                
    return {
        "metadata": metadata,
        "sections": sections
    }
