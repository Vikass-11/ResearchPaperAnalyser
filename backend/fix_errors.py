import sys

def run():
    with open('app/api/literature.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Generic result["error"]
    content = content.replace(
        'raise HTTPException(status_code=500, detail=result["error"])',
        'raise HTTPException(status_code=500, detail={"error": {"code": "INTERNAL_ERROR", "message": result["error"]}})'
    )
    
    # Gap generation error
    content = content.replace(
        'raise HTTPException(status_code=status_code, detail=result["error"])',
        'raise HTTPException(status_code=status_code, detail={"error": {"code": "PROCESSING_FAILED", "message": result["error"]}})'
    )

    with open('app/api/literature.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    with open('app/api/papers.py', 'r', encoding='utf-8') as f:
        content_papers = f.read()
        
    # Papers specific error
    content_papers = content_papers.replace(
        'raise HTTPException(status_code=400, detail="Only PDF files are allowed")',
        'raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": "Only PDF files are allowed."}})'
    )
    content_papers = content_papers.replace(
        'raise HTTPException(status_code=404, detail="Paper not found")',
        'raise HTTPException(status_code=404, detail={"error": {"code": "PAPER_NOT_FOUND", "message": "Paper not found."}})'
    )
    with open('app/api/papers.py', 'w', encoding='utf-8') as f:
        f.write(content_papers)

if __name__ == "__main__":
    run()
