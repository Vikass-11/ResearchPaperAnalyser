import asyncio
from app.models.database import SessionLocal
from app.models.schema import Paper
from app.api.papers import process_paper_background

async def main():
    db = SessionLocal()
    # take the last paper
    paper = db.query(Paper).order_by(Paper.id.desc()).first()
    if not paper:
        print("no paper")
        return
    print(f"Testing paper {paper.id}: {paper.title}")
    
    # Run the background process to see what exception it throws
    await process_paper_background(paper.id, paper.file_path, db)

if __name__ == "__main__":
    asyncio.run(main())
