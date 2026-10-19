from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

TEMPLATE = r"c:\Users\REALME\OneDrive\Desktop\FRAUD_DETECTION\PROJECT WORK REVIEW 2 PPT TEMPLATE.pptx"
OUTPUT = r"c:\Users\REALME\OneDrive\Desktop\FRAUD_DETECTION\PROJECT_WORK_REVIEW_2_PPT_TEMPLATE_filled.pptx"

STUDENT_NAME = "Shambhu Pandey"
REG_NO = "25MCA1020"
GUIDE_NAME = "Tamilrashi"

prs = Presentation(TEMPLATE)

# Helper to add a titled bullet slide
def add_bullet_slide(title, bullets):
    layout = prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]
    slide = prs.slides.add_slide(layout)
    slide.shapes.title.text = title
    tf = slide.shapes.placeholders[1].text_frame
    tf.clear()
    for i, b in enumerate(bullets):
        if i == 0:
            tf.text = b
        else:
            p = tf.add_paragraph()
            p.text = b
            p.level = 0
    return slide

# 1. ABSTRACT (max 200 words)
add_bullet_slide("1. ABSTRACT", [
    "Fraud detection: identifying suspicious transactions indicating theft or abuse.",
    "Problem: financial fraud is increasing; rule-based systems miss novel attacks.",
    "Solution: ML classifiers (Random Forest, XGBoost, Autoencoder) + preprocessing + threshold tuning.",
    "Outcome: automated system flags likely fraud, outputs risk score and explanations.",
    "[SPACE FOR OUTPUT SCREENSHOT]"
])

# 2. INTRODUCTION (max 150 words)
add_bullet_slide("2. INTRODUCTION", [
    "Fraud detection finds transactions that deviate from normal behaviour.",
    "Important to prevent financial loss and preserve customer trust.",
    "Real-world use: banks, payment gateways, e-commerce, UPI services.",
    "Project includes a Streamlit dashboard for live prediction and explainability."
])

# 3. LITERATURE SURVEY (table) — create as bullet list summarizing table rows
lit_rows = [
    "1. ML for Fraud Detection — Techniques: LR, RF — Findings: Ensembles improve accuracy — Limit: Data imbalance",
    "2. Boosted Trees in Fraud — Techniques: XGBoost — Findings: High precision & recall — Limit: Needs tuning",
    "3. Anomaly Detection with AE — Techniques: Autoencoder — Findings: Detects novel frauds — Limit: Needs large data",
    "4. SMOTE for Imbalance — Techniques: SMOTE + classifiers — Findings: Improves recall — Limit: Possible overfitting",
    "5. Explainable Fraud Models — Techniques: SHAP/LIME — Findings: Builds auditor trust — Limit: Computationally heavy",
    "6. Real-time Fraud Systems — Techniques: Stream processing + ML — Findings: Low-latency detection possible — Limit: Engineering complexity",
]
add_bullet_slide("3. LITERATURE SURVEY", lit_rows)

# 4. RESEARCH GAPS
add_bullet_slide("4. RESEARCH GAPS", [
    "Low detection accuracy on emerging fraud types.",
    "Severe class imbalance: fraud << legitimate.",
    "High false positives cause user friction.",
    "Lack of explainability and deployable pipelines."
])

# 5. OBJECTIVES
add_bullet_slide("5. OBJECTIVES", [
    "Detect fraudulent transactions using ML.",
    "Improve recall and F1-score.",
    "Handle imbalanced datasets robustly.",
    "Provide near real-time prediction."
])

# 6. MODULE IDENTIFICATION
add_bullet_slide("6. MODULE IDENTIFICATION", [
    "Data Collection: PaySim, CICIDS, IEEE, BankSim, uploads.",
    "Data Preprocessing: cleaning, imputation, scaling, leakage removal.",
    "Feature Engineering: time, device, aggregates, encodings.",
    "Model Training: LR, RF, XGBoost, Isolation Forest, Autoencoder.",
    "Prediction System: thresholding, scoring, persistence.",
    "UI: Streamlit dashboard (train/demo/explain)."
])

# 7. SYSTEM ARCHITECTURE
add_bullet_slide("7. SYSTEM ARCHITECTURE", [
    "Flow: User Input → Preprocessing → Model → Prediction → Output (risk + explanation).",
    "Components: Data Loader → Preprocessor → Model Service → UI.",
    "Tech stack: Python, scikit-learn, XGBoost, imbalanced-learn, SHAP, Streamlit.",
    "[SPACE FOR ARCHITECTURE DIAGRAM]"
])

# 8. DEVELOPMENT & INTEGRATION
add_bullet_slide("8. DEVELOPMENT & INTEGRATION", [
    "Model building: pipeline with CV, hyperparameter tuning, threshold selection.",
    "Integration: save models/metrics in models/, wire Streamlit UI to model.",
    "Problems: data leakage, imbalance, mismatched features.",
    "Solutions: remove leakage cols, SMOTE/Tomek, schema validation."
])

# 9. PROTOTYPE / FRAMEWORK
add_bullet_slide("9. PROTOTYPE / FRAMEWORK", [
    "Working flow: select/upload dataset → preprocess → train/choose model → live predict.",
    "Live prediction: sample transaction input → model returns probability + SHAP explanation.",
    "Run demo: streamlit run app.py → open http://localhost:8501.",
    "[SPACE FOR DEMO SCREENSHOT]"
])

# 10. OUTCOME
add_bullet_slide("10. OUTCOME", [
    "Fraud transactions successfully detected in prototype.",
    "Real-time prediction and risk scoring functional.",
    "Multi-dataset support and model comparisons available.",
    "Explainability (SHAP/LIME) present for each prediction."
])

# 11. RESULTS
add_bullet_slide("11. RESULTS", [
    "Example metrics (PaySim): RF — Acc 0.931; Prec 0.998; Rec 0.997; F1 0.998.",
    "XGBoost — Acc 0.987; Prec 0.994; Rec 0.997; F1 0.995.",
    "Logistic Regression — baseline: good recall, lower precision.",
    "Confusion matrix explained: TP detected fraud; FP legitimate flagged; FN missed fraud; TN correct legit."
])

# 12. TIMELINE
add_bullet_slide("12. TIMELINE", [
    "Week 1: Dataset collection and EDA.",
    "Week 2: Data cleaning, preprocessing, feature engineering.",
    "Week 3: Model training, CV, threshold tuning.",
    "Week 4: Testing, evaluation, explainability integration.",
    "Week 5: UI (Streamlit) development and demo prep."
])

# 13. REFERENCES
add_bullet_slide("13. REFERENCES", [
    "Bolton, R. J., & Hand, D. J. (2002). Statistical fraud detection: A review. Journal of Financial Crime.",
    "Ngai, E. W. T., et al. (2011). The application of data mining techniques in financial fraud detection. Decision Support Systems.",
    "Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. KDD Proceedings.",
    "Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. NIPS Workshop.",
    "Chawla, N. V., et al. (2002). SMOTE. Journal of AI Research."
])

# Add footer with student details on first slide
if prs.slides:
    first = prs.slides[0]
    left = Inches(0.5)
    top = Inches(6.6)
    width = Inches(9)
    height = Inches(0.5)
    tx = first.shapes.add_textbox(left, top, width, height)
    tx.text_frame.text = f"Name: {STUDENT_NAME}    Reg No: {REG_NO}    Guide: {GUIDE_NAME}"

prs.save(OUTPUT)
print(f"Saved filled PPT to: {OUTPUT}")
