from pydantic import BaseModel, Field
from typing import List

class ResearchProfileSchema(BaseModel):
    research_domain: str = Field(description="The primary academic domain (e.g. Computer Science, Artificial Intelligence)")
    sub_domains: List[str] = Field(description="Specific subdomains (e.g. ['Computer Vision', 'Deep Learning'])", default_factory=list)
    research_topic: str = Field(description="Concise academic research topic (e.g. 'Deep Learning-Based Diabetic Retinopathy Detection')")
    research_problem: str = Field(description="Academically accurate description of the problem being solved")
    research_objective: str = Field(description="What the researchers are trying to achieve")
    methodology: str = Field(description="Summary of the overall methodology used")
    methods: List[str] = Field(description="Specific research methods (e.g. ['Transfer Learning', 'Image Classification'])", default_factory=list)
    algorithms: List[str] = Field(description="Algorithms explicitly used (e.g. ['Random Forest', 'CNN'])", default_factory=list)
    models: List[str] = Field(description="ML/DL models or architectures (e.g. ['ResNet50', 'BERT'])", default_factory=list)
    technologies: List[str] = Field(description="Technologies explicitly mentioned (e.g. ['Python', 'PyTorch'])", default_factory=list)
    datasets: List[str] = Field(description="Datasets explicitly used (e.g. ['ImageNet'])", default_factory=list)
    key_concepts: List[str] = Field(description="Important academic concepts (e.g. ['feature extraction'])", default_factory=list)
    keywords: List[str] = Field(description="8-15 high-value academic search keywords", default_factory=list)
    research_questions: List[str] = Field(description="Explicit or derived research questions", default_factory=list)
    application_domain: str = Field(description="Practical application area (e.g. 'Healthcare') or 'Not explicitly stated'")
