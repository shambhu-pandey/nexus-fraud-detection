import json
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import config

TEMPLATE = r"c:\Users\REALME\OneDrive\Desktop\FRAUD_DETECTION\PROJECT WORK REVIEW 2 PPT TEMPLATE.pptx"
OUTPUT = r"c:\Users\REALME\OneDrive\Desktop\FRAUD_DETECTION\Shambhu_Pandey_Project_Full.pptx"
STUDENT_NAME = "Shambhu Pandey"
REG_NO = "25MCA1020"
GUIDE_NAME = "Tamilrashi"

# Load evaluation metrics
with open(r"c:\Users\REALME\OneDrive\Desktop\FRAUD_DETECTION\models\evaluation_metrics.json", "r") as f:
    eval_metrics = json.load(f)

# Choose dataset to present (paysim if available)
dataset_key = 'paysim' if 'paysim' in eval_metrics else list(eval_metrics.keys())[0]
dataset_meta = config.DATASET_META.get(dataset_key, {})

prs = Presentation(TEMPLATE)

# Add footer/contact box on first slide (overwrite if exists)
if prs.slides:
    slide = prs.slides[0]
    left = Inches(0.5)
    top = Inches(6.6)
    width = Inches(9)
    height = Inches(0.5)
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.text = f"Name: {STUDENT_NAME}    Reg No: {REG_NO}    Guide: {GUIDE_NAME}"
    for paragraph in tf.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0, 0, 0)

# Helper to add bullet slide
def add_bullet_slide(title, bullets):
    layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = title
    body = slide.shapes.placeholders[1].text_frame
    body.clear()
    for i, b in enumerate(bullets):
        if i == 0:
            body.text = b
        else:
            p = body.add_paragraph()
            p.text = b
            p.level = 0
    return slide

# Objective slide
add_bullet_slide("Objective", [
    "Build a real-time fraud detection dashboard with UPI simulation",
    "Support multiple datasets (PaySim, CICIDS, IEEE, BankSim)",
    "Provide explainability (SHAP/LIME) and digital twin simulations",
])

# Dataset slide
dataset_bullets = [
    f"Dataset: {dataset_meta.get('display_name', dataset_key)}",
    f"Source file: {dataset_meta.get('file', 'data/...')}",
    f"Target column: {dataset_meta.get('target_col', 'isFraud')}",
    f"Sample size (default): {dataset_meta.get('sample_size', 'varies')}"
]
add_bullet_slide("Dataset & Preprocessing", dataset_bullets)

# Methodology slide
add_bullet_slide("Methodology", [
    "Data preprocessing: imputation, normalization, leakage removal",
    "Imbalance handling: SMOTE / resampling",
    "Models: Logistic Regression, Random Forest, XGBoost, Isolation Forest, Autoencoder",
    "Model selection via cross-validation and metrics (Precision/Recall/F1/ROC-AUC)"
])

# Models & Results slide(s)
# Summarize top models for chosen dataset
results = eval_metrics.get(dataset_key, {}).get('results', {})
best_model = eval_metrics.get(dataset_key, {}).get('best_model', None)
if not best_model and results:
    # pick model with highest F1
    best_model = max(results.items(), key=lambda kv: kv[1].get('F1-Score', 0))[0]

model_summary = [f"Dataset: {dataset_meta.get('display_name', dataset_key)}"]
if best_model:
    model_summary.append(f"Recommended model: {best_model}")

# Add each model metric as bullets
for mname, mvals in results.items():
    acc = mvals.get('Accuracy')
    prec = mvals.get('Precision')
    rec = mvals.get('Recall')
    f1 = mvals.get('F1-Score')
    thr = mvals.get('Best_Threshold')
    model_summary.append(f"{mname} — Acc: {acc:.3f}, Prec: {prec:.3f}, Rec: {rec:.3f}, F1: {f1:.3f}, Thr: {thr}")

add_bullet_slide("Models & Key Results", model_summary)

# Add a slide pointing to saved artifacts
add_bullet_slide("Artifacts & Files", [
    "Saved models: models/ (timestamps + names)",
    "Evaluation metrics: models/evaluation_metrics.json",
    "Selected thresholds: models/thresholds_selected.json",
    "Prediction checks: models/prediction_checks.csv"
])

# Demo slide (placeholder)
blank_layout = None
for layout in prs.slide_layouts:
    if not layout.placeholders:
        blank_layout = layout
        break
if blank_layout is None:
    blank_layout = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[-1]

slide = prs.slides.add_slide(blank_layout)
# Title
title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(9.0), Inches(0.6))
tf = title_box.text_frame
tf.text = "Demo — Project Screenshot"
for paragraph in tf.paragraphs:
    for run in paragraph.runs:
        run.font.size = Pt(24)
        run.font.color.rgb = RGBColor(0, 0, 0)

ph = slide.shapes.add_textbox(Inches(1.0), Inches(1.4), Inches(8.0), Inches(4.8))
tf2 = ph.text_frame
tf2.text = "[PASTE DEMO PROJECT SCREENSHOT HERE]"
for paragraph in tf2.paragraphs:
    for run in paragraph.runs:
        run.font.size = Pt(18)
        run.font.color.rgb = RGBColor(128, 128, 128)

# Conclusions & Future Work
add_bullet_slide("Conclusions & Future Work", [
    "High-performing models achieved strong recall and precision on PaySim",
    "Threshold tuning provides business-driven trade-offs between FP/FN",
    "Future: deploy model endpoint, online learning, drift monitoring"
])

# Acknowledgements
add_bullet_slide("Acknowledgements", [
    f"Student: {STUDENT_NAME}",
    f"Guide: {GUIDE_NAME}",
    "Tools: Streamlit, scikit-learn, XGBoost, SHAP, LIME"
])

prs.save(OUTPUT)
print(f"Saved final presentation to: {OUTPUT}")
