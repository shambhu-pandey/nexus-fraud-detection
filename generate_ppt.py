from pptx import Presentation
from pptx.util import Inches, Pt
import os

def add_bullets(shape, text_list, size=18):
    tf = shape.text_frame
    tf.clear()
    for i, item in enumerate(text_list):
        p = tf.add_paragraph()
        if isinstance(item, tuple):
            # For the 8 points with "Need" format
            title, detail, need = item
            run = p.add_run()
            run.text = f"{i+1}. {title}"
            run.font.bold = True
            run.font.size = Pt(size)
            
            p2 = tf.add_paragraph()
            p2.text = detail
            p2.level = 1
            p2.font.size = Pt(size - 4)
            
            p3 = tf.add_paragraph()
            p3.text = f"Need: {need}"
            p3.level = 1
            p3.font.size = Pt(size - 4)
            p3.font.italic = True
        else:
            p.text = item
            p.level = 0
            p.font.size = Pt(size)
        p.font.name = 'Times New Roman'

def main():
    template_path = 'PROJECT WORK REVIEW 2 PPT TEMPLATE.pptx'
    output_path = 'FRAUD_DETECTION_SHAMBHU_FINAL.pptx'
    
    if not os.path.exists(template_path):
        print(f"Error: Template {template_path} not found.")
        return

    prs = Presentation(template_path)

    # ... [Assuming Slide 1-7 are already handled or we focus on Research Gaps] ...
    # Slide 1: Title
    slide1 = prs.slides[0]
    for shape in slide1.shapes:
        if not hasattr(shape, "text"): continue
        if "<<PROJECT TITLE" in shape.text:
            shape.text = "Digital Twin–Enabled Framework for Forecasting and Mitigating Fraud with UPI Integration"
        elif "<<STUDENT NAME" in shape.text:
            shape.text = "SHAMBHU PANDEY (25MCA1020)"
        elif "<<M.Tech" in shape.text:
            shape.text = "Master of Computer Applications (MCA)"
        elif "<<GUIDE NAME>>" in shape.text:
            shape.text = "TAMILRASHI"
        elif "<<GUIDE DESIGNATION>>" in shape.text:
            shape.text = "Professor"

    # Slide 8 & 9: Research Gaps (Splitting 8 points across two slides if needed, or one)
    research_gaps = [
        ("few Single System Combines Digital Twin, AI, and Fraud Detection", 
         "Most papers focus on either Digital Twin or AI separately.", 
         "A complete system that uses simulation (Digital Twin) and learning (AI) together."),
        ("Focus on Smart Cities, few on Financial Fraud", 
         "Many studies apply Digital Twins to traffic or IoT. Very few target banking transactions.", 
         "More research focused on financial fraud environments."),
        ("Lack of Explainability in AI Models", 
         "Most AI models act like black boxes — they give results but don’t explain why.", 
         "Integration of Explainable AI tools like SHAP and LIME to clarify decisions."),
        ("Real-Time Fraud Detection is Rare", 
         "Many systems detect fraud after it happens, which is too late.", 
         "Real-time, adaptive fraud detection systems."),
        ("Lack of Proper Testing on Financial Datasets", 
         "Most papers use general cybersecurity datasets like KDD Cup.", 
         "Testing and validation using realistic financial transaction data like PaySim/CICIDS2017."),
        ("High False Positives in Detection Systems", 
         "Many models wrongly flag normal transactions as fraud, causing dissatisfaction.", 
         "Smarter models that reduce false alarms and improve precision."),
        ("Poor Adaptability to Evolving Fraud Techniques", 
         "Fraud patterns keep changing. Most systems don’t learn or adapt automatically.", 
         "Use of adaptive learning models and continuous monitoring."),
        ("Lack of Modular and Reusable Design", 
         "Most systems are built for one specific domain and are hard to scale.", 
         "Modular architecture that supports reuse and scalability across industries.")
    ]

    # Slide 8 (First 4 Gaps)
    slide8 = prs.slides[7]
    for shape in slide8.shapes:
        if hasattr(shape, "text") and ("4." in shape.text or "RESEARCH GAPS" in shape.text):
            # Clear or find the content shape
            pass
        elif hasattr(shape, "text_frame"):
            if "|" not in shape.text: # Avoid header/footer
                add_bullets(shape, research_gaps[:4], size=16)

    # Slide 9 (Next 4 Gaps)
    # We might need to duplicate slide 8 if slide 9 isn't already a gap slide
    # But for simplicity, let's assume Slide 9 is the continuation slide
    slide9 = prs.slides[8] 
    for shape in slide9.shapes:
        if hasattr(shape, "text_frame") and "|" not in shape.text:
             add_bullets(shape, research_gaps[4:], size=16)

    prs.save(output_path)
    print(f"Final PPT with 8 Research Gaps saved to {output_path}")

if __name__ == "__main__":
    main()
