import fitz
import os

os.makedirs("../test_pdfs", exist_ok=True)

samples = [
    {
        "filename": "Sample_1_Quantum_Computing.pdf",
        "title": "Quantum Error Correction in Near-Term Devices",
        "content": "Abstract: We propose a novel quantum error correction algorithm optimized for noisy intermediate-scale quantum (NISQ) devices. \n\nMethodology: We simulated a 16-qubit surface code under realistic decoherence models. \n\nResults: Our approach demonstrates a 15% improvement in fidelity over standard Shor encoding. \n\nFuture work will scale this to 64 qubits."
    },
    {
        "filename": "Sample_2_Medical_AI.pdf",
        "title": "Deep Learning for Early Melanoma Detection",
        "content": "Abstract: This paper introduces a CNN-based architecture for identifying early-stage melanoma from dermoscopy images. \n\nMethodology: We trained a ResNet-50 model on the ISIC 2019 dataset, utilizing transfer learning. \n\nResults: The model achieved an accuracy of 96.4% and an AUC of 0.98. \n\nLimitation: The dataset lacks diverse skin tones."
    },
    {
        "filename": "Sample_3_Climate_Science.pdf",
        "title": "Impact of Ocean Acidification on Coral Bleaching",
        "content": "Abstract: We investigate the accelerating rate of coral bleaching in the Great Barrier Reef. \n\nMethodology: We analyzed sea surface temperature data and pH levels from 2000 to 2023. \n\nResults: A direct correlation was found between pH drops below 8.1 and mass bleaching events. \n\nContribution: We provide the first high-resolution mapping of acidification zones."
    },
    {
        "filename": "Sample_4_Material_Science.pdf",
        "title": "Tensile Strength of Graphene-Infused Polymers",
        "content": "Abstract: We evaluate the structural integrity of novel graphene-infused epoxy resins. \n\nMethodology: Standardized tensile stress testing was performed on 50 composite samples. \n\nResults: The addition of 0.5% graphene oxide increased tensile strength by 42%. \n\nConclusion: These composites are highly viable for aerospace applications."
    }
]

for sample in samples:
    doc = fitz.open()  
    page = doc.new_page()
    
    text = f"Title: {sample['title']}\n\n{sample['content']}"
    
    page.insert_textbox(fitz.Rect(50, 50, 500, 800), text, fontsize=12)
    
    path = os.path.join("../test_pdfs", sample["filename"])
    doc.save(path)
    doc.close()
    print(f"Created {path}")
