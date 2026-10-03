import asyncio
from app.models.database import SessionLocal
from app.models.schema import Paper, ResearchProfile

def inject_profile():
    db = SessionLocal()
    try:
        paper = db.query(Paper).first()
        if not paper:
            paper = Paper(
                title="A Comparative performance evaluation of a complex-order PI",
                authors=["Test Author"],
                abstract="Test abstract for complex-order PI controllers in deep learning.",
                year=2023,
                doi="10.1234/test.paper",
                processing_status="COMPLETED"
            )
            db.add(paper)
            db.commit()
            print("Created dummy paper.")
            
        profile = db.query(ResearchProfile).filter(ResearchProfile.paper_id == paper.id).first()
        if not profile:
            profile = ResearchProfile(
                paper_id=paper.id,
                research_domain="Computer Science",
                sub_domains=["Deep Learning", "Medical Image Analysis"],
                research_topic="Deep Learning-Based Diabetic Retinopathy Detection",
                research_problem="Lack of explainability in AI models for medical imaging.",
                research_objective="To introduce an explainable AI framework for diabetic retinopathy.",
                methodology="Transfer learning with a pretrained ResNet.",
                methods=["Transfer Learning", "Image Classification"],
                algorithms=["CNN", "Random Forest"],
                models=["ResNet50"],
                technologies=["PyTorch"],
                datasets=["ImageNet"],
                key_concepts=["XAI", "feature extraction"],
                keywords=["diabetic retinopathy detection", "retinal fundus images", "deep learning"],
                research_questions=[],
                application_domain="Healthcare"
            )
            db.add(profile)
            db.commit()
            print(f"Injected mock Research Profile for paper ID {paper.id}.")
        else:
            print("Profile already exists.")
            
    finally:
        db.close()

if __name__ == "__main__":
    inject_profile()
