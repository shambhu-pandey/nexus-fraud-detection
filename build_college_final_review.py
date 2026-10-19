"""Fill the supplied VIT Chennai final-review template with project-verified content."""
from __future__ import annotations

import json
import os
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parent
TEMPLATE = Path(r"C:\Users\shamb\Downloads\PROJECT WORK FINAL REVIEW PPT TEMPLATE.pptx")
OUTPUT = ROOT / "Nexus_Fraud_Defense_Final_Review_Rev2_Aligned.pptx"
METRICS_PATH = ROOT / "models" / "evaluation_metrics.json"
STATS_PATH = ROOT / "models" / "dataset_stats.json"

# Clean college-template-friendly palette, coordinated with the Nexus dashboard.
NAVY = RGBColor(25, 50, 77)
BLUE = RGBColor(18, 130, 190)
CYAN = RGBColor(34, 170, 210)
TEAL = RGBColor(36, 143, 132)
GREEN = RGBColor(46, 139, 87)
AMBER = RGBColor(214, 145, 32)
RED = RGBColor(187, 65, 65)
INK = RGBColor(43, 55, 68)
MUTED = RGBColor(99, 112, 126)
PALE = RGBColor(239, 246, 250)
PALE_BLUE = RGBColor(229, 242, 250)
PALE_GREEN = RGBColor(232, 245, 238)
PALE_AMBER = RGBColor(251, 245, 230)
WHITE = RGBColor(255, 255, 255)
LINE = RGBColor(207, 220, 229)
FONT = "Arial"


def remove_shape(shape):
    element = shape._element
    element.getparent().remove(element)


def named(slide, name):
    return next(shape for shape in slide.shapes if shape.name == name)


def replace_text(shape, text, *, size=20, color=INK, bold=False,
                 font=FONT, align=None, valign=MSO_ANCHOR.TOP,
                 margins=(0.12, 0.12, 0.08, 0.08)):
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.vertical_anchor = valign
    tf.margin_left = Inches(margins[0])
    tf.margin_right = Inches(margins[1])
    tf.margin_top = Inches(margins[2])
    tf.margin_bottom = Inches(margins[3])
    p = tf.paragraphs[0]
    if align is not None:
        p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shape


def add_text(slide, x, y, w, h, text, *, size=18, color=INK, bold=False,
             align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.MIDDLE,
             font=FONT, margin=0.06, fill=None):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
        shape.line.fill.background()
    return replace_text(shape, text, size=size, color=color, bold=bold,
                        font=font, align=align, valign=valign,
                        margins=(margin, margin, margin, margin))


def add_paragraphs(slide, x, y, w, h, rows, *, size=17, color=INK,
                   bullet=False, font=FONT, gap=8, fill=None,
                   margins=(0.12, 0.12, 0.1, 0.1)):
    shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
        shape.line.color.rgb = LINE
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.margin_left, tf.margin_right = Inches(margins[0]), Inches(margins[1])
    tf.margin_top, tf.margin_bottom = Inches(margins[2]), Inches(margins[3])
    for i, row in enumerate(rows):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.level = 0
        r = p.add_run()
        r.text = ("• " if bullet else "") + row
        r.font.name = font
        r.font.size = Pt(size)
        r.font.color.rgb = color
    return shape


def card(slide, x, y, w, h, title, body, *, color=BLUE, fill=WHITE,
         title_size=16, body_size=13.5, title_color=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = LINE
    sh.line.width = Pt(1)
    # colored accent rail
    rail = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  Inches(x), Inches(y), Inches(0.09), Inches(h))
    rail.fill.solid()
    rail.fill.fore_color.rgb = color
    rail.line.fill.background()
    add_text(slide, x + 0.18, y + 0.08, w - 0.29, 0.34, title,
             size=title_size, color=title_color or color, bold=True,
             valign=MSO_ANCHOR.MIDDLE, margin=0.01)
    add_text(slide, x + 0.18, y + 0.47, w - 0.30, h - 0.53, body,
             size=body_size, color=INK, valign=MSO_ANCHOR.TOP, margin=0.01)
    return sh


def arrow(slide, x, y, w=0.38, h=0.32, color=CYAN):
    sh = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                                Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return sh


def rounded_box(slide, x, y, w, h, title, body, *, fill=PALE_BLUE,
                color=BLUE, title_size=15, body_size=11.5):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.color.rgb = color
    sh.line.width = Pt(1.25)
    add_text(slide, x + .07, y + .05, w - .14, .36, title,
             size=title_size, color=color, bold=True, align=PP_ALIGN.CENTER,
             margin=.01)
    add_text(slide, x + .12, y + .43, w - .24, h - .50, body,
             size=body_size, color=INK, align=PP_ALIGN.CENTER,
             valign=MSO_ANCHOR.MIDDLE, margin=.02)
    return sh


def footer(slide, text, *, y=7.02, size=7.4):
    add_text(slide, .62, y, 12.7, .28, text, size=size, color=MUTED,
             valign=MSO_ANCHOR.MIDDLE, margin=0.01)


def add_slide_title(slide, text):
    shape = next((s for s in slide.shapes if s.name == "Title 1"), None)
    if shape:
        shape.text = text
        for p in shape.text_frame.paragraphs:
            for r in p.runs:
                r.font.name = FONT
                r.font.bold = True
    return shape


def metrics_row(metrics, stats, key, label):
    ds = metrics[key]
    best = ds["best_model"]
    score = ds["results"][best]
    st = stats[key]
    return {
        "dataset": label,
        "best": best,
        "accuracy": score["Accuracy"],
        "precision": score["Precision"],
        "recall": score["Recall"],
        "f1": score["F1-Score"],
        "auc": score["ROC-AUC"],
        "threshold": score["Best_Threshold"],
        "rows": st["rows_used"],
        "fraud": st["sampled_fraud_count"],
        "ratio": st["sampled_fraud_ratio"],
    }


def fill_cover(prs):
    slide = prs.slides[0]
    title = named(slide, "Title 1")
    replace_text(title,
                 "DIGITAL TWIN-ENABLED FRAMEWORK\nFOR FORECASTING AND MITIGATING FRAUD",
                 size=31, color=NAVY, bold=True, align=PP_ALIGN.CENTER,
                 valign=MSO_ANCHOR.MIDDLE, margins=(.22, .22, .04, .04))
    body = named(slide, "Subtitle 2")
    tf = body.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(.18); tf.margin_right = Inches(.18)
    lines = [
        ("MCA PROJECT WORK FINAL REVIEW", 18, True),
        ("Presented by", 15, False),
        ("SHAMBHU PANDEY  |  25MCA1020", 19, True),
        ("Master of Computer Applications (MCA)", 15, False),
        ("Under the Guidance of", 15, False),
        ("DR. TAMILARASI K  |  Assistant Professor Sr. Grade 1", 16, True),
        ("School of Computer Science and Engineering", 14, False),
        ("Vellore Institute of Technology, Chennai", 14, False),
    ]
    for i, (text, size, bold) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        p.space_after = Pt(5 if i in (0, 2, 5) else 2)
        run = p.add_run(); run.text = text
        run.font.name = FONT; run.font.size = Pt(size); run.font.bold = bold
        run.font.color.rgb = NAVY if bold else INK


def fill_contents(prs):
    slide = prs.slides[1]
    add_slide_title(slide, "CONTENTS")
    shape = named(slide, "Content Placeholder 2")
    rows = [
        "1. Abstract", "2. Introduction", "3. Literature Survey",
        "3. Literature Survey (continued)", "4. Research Gaps", "5. Objectives",
        "Review-II Objectives: Progress and Next Work", "6. Module Identification",
        "7. System Architecture", "8. Development & Integration",
        "9. Prototype / Research Framework", "10. Project Conclusion", "10. Outcome: Best Models",
        "Dataset Profiles and Full Model Results", "11. Results: Holdout Evaluation",
        "12. Timeline / Next Milestones", "13. References",
    ]
    replace_text(shape, "\n".join(rows), size=17, color=INK,
                 margins=(1.0, .35, .14, .08))


def fill_abstract(prs):
    slide = prs.slides[2]
    add_slide_title(slide, "1. ABSTRACT")
    shape = named(slide, "Content Placeholder 2")
    text = (
        "The rapid growth of digital payments has increased the need for timely fraud analysis. "
        "This project develops Nexus Fraud Defense, a Streamlit prototype for preparing and "
        "evaluating PaySim, BankSim, IEEE-CIS, and CICIDS2017 data. Dataset-specific feature "
        "pipelines clean and transform records, then train Logistic Regression, Random Forest, "
        "XGBoost, and Isolation Forest models. Holdout evaluation reports precision, recall, F1, "
        "ROC-AUC, confusion counts, and decision thresholds so rare-event trade-offs remain visible. "
        "The dashboard includes data management, model evaluation, a scenario simulator, manual "
        "example prediction, and executive insights. The simulator uses configured state-transition "
        "probabilities and a heuristic intervention; it is not a data-calibrated or live digital twin. "
        "Saved results demonstrate a working research prototype, not production performance."
    )
    replace_text(shape, text, size=21, color=INK, font="Times New Roman",
                 valign=MSO_ANCHOR.MIDDLE, margins=(.4, .4, .16, .16))


def fill_introduction(prs):
    slide = prs.slides[3]
    add_slide_title(slide, "2. INTRODUCTION")
    shape = named(slide, "Content Placeholder 2")
    text = (
        "The expansion of digital payments, wallets, and online commerce creates more opportunities "
        "for fraudulent use of accounts and payment instruments. This project follows the Review-II "
        "aim of building a multi-model framework for forecasting and mitigating fraud, while making "
        "the prototype's current scope clear. It prepares PaySim and BankSim transaction simulators, "
        "the IEEE-CIS e-commerce benchmark, and CICIDS2017 network traffic as separate tasks. It "
        "compares supervised classifiers with an unsupervised anomaly detector and exposes the "
        "precision-recall and threshold trade-offs through a Streamlit dashboard. The digital-twin "
        "component is currently a configurable scenario simulator; it is not synchronized to a live "
        "payment service or trained to forecast real attacker behavior. The project therefore "
        "demonstrates an integrated research workflow, with external, temporal, explainability, and "
        "operational validation left as next steps."
    )
    remove_shape(shape)
    add_text(slide, .93, 1.98, 12.1, 4.25, text, size=22, color=INK,
             valign=MSO_ANCHOR.MIDDLE, margin=.08)
    add_text(slide, .62, 6.34, 12.7, .80,
             "[1] R. J. Bolton and D. J. Hand, “Statistical Fraud Detection: A Review,” Statistical Science, vol. 17, no. 3, pp. 235–249, 2002.\n"
             "[2] E. A. Lopez-Rojas, A. Elmir, and S. Axelsson, “PaySim: A Financial Mobile Money Simulator for Fraud Detection,” EMSS, 2016.\n"
             "[3] E. A. Lopez-Rojas and S. Axelsson, “BankSim: A Bank Payments Simulator for Fraud Detection Research,” EMSS, 2014.\n"
             "[13] I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, “Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization,” ICISSP, 2018. [14] IEEE-CIS Fraud Detection, Kaggle, 2019.",
             size=7.7, color=MUTED, valign=MSO_ANCHOR.MIDDLE, margin=.012)


def fill_literature(prs):
    slide = prs.slides[4]
    add_slide_title(slide, "3. LITERATURE SURVEY")
    table_shape = next(sh for sh in slide.shapes if sh.has_table)
    table = table_shape.table
    headers = ["S.No", "Article Title", "Techniques Used", "Key Findings", "Limitations"]
    for j, value in enumerate(headers):
        cell = table.cell(0, j); cell.text = value
    rows = [
        ["1", "Bolton & Hand (2002) [1]", "Statistical fraud detection review", "Frames fraud as a rare, adaptive detection problem.", "Review paper; results depend on domain data and evaluation."],
        ["2", "PaySim (2016) + BankSim (2014) [2], [3]", "Agent-based transaction simulators", "Provide shareable labeled data for studying payment fraud.", "Synthetic transactions do not guarantee transfer to observed or future data."],
        ["3", "Chen & Guestrin (2016), XGBoost [4]", "Regularized gradient-boosted trees", "Scalable tree boosting for structured prediction tasks.", "Requires tuning; ranking performance does not set an operating threshold."],
        ["4", "Liu, Ting & Zhou (2008), Isolation Forest [5]", "Unsupervised isolation-based anomaly detection", "Finds unusual records without supervised labels at fit time.", "Anomaly is not the same as fraud; anomaly scores need careful interpretation."],
    ]
    widths = [0.55, 2.45, 2.45, 3.35, 3.75]
    for j, width in enumerate(widths):
        table.columns[j].width = Inches(width)
    for i, row in enumerate(rows, start=1):
        for j, value in enumerate(row):
            table.cell(i, j).text = value
    table.rows[0].height = Inches(.48)
    for i in range(1, len(table.rows)):
        table.rows[i].height = Inches(1.0)
    for r, row in enumerate(table.rows):
        for c, cell in enumerate(row.cells):
            cell.margin_left = Inches(.07); cell.margin_right = Inches(.06)
            cell.margin_top = Inches(.035); cell.margin_bottom = Inches(.035)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER if c == 0 else PP_ALIGN.LEFT
                p.space_after = Pt(0)
                for run in p.runs:
                    run.font.name = FONT
                    run.font.size = Pt(10.5 if r else 11.5)
                    run.font.bold = r == 0
                    run.font.color.rgb = WHITE if r == 0 else INK
            if r == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
    add_text(slide, .62, 6.39, 12.7, .78,
             "[1] R. J. Bolton and D. J. Hand, “Statistical Fraud Detection: A Review,” Statistical Science, vol. 17, no. 3, pp. 235–249, 2002.\n"
             "[2] E. A. Lopez-Rojas, A. Elmir, and S. Axelsson, “PaySim: A Financial Mobile Money Simulator for Fraud Detection,” EMSS, 2016.\n"
             "[3] E. A. Lopez-Rojas and S. Axelsson, “BankSim: A Bank Payments Simulator for Fraud Detection Research,” EMSS, 2014.\n"
             "[4] T. Chen and C. Guestrin, “XGBoost: A Scalable Tree Boosting System,” Proc. ACM SIGKDD, pp. 785–794, 2016.\n"
             "[5] F. T. Liu, K. M. Ting, and Z.-H. Zhou, “Isolation Forest,” Proc. IEEE ICDM, pp. 413–422, 2008.\n"
             "[13] I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, “Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization,” ICISSP, 2018.\n"
             "[14] IEEE Computational Intelligence Society, “IEEE-CIS Fraud Detection,” Kaggle competition, 2019.",
             size=7.2, color=MUTED, valign=MSO_ANCHOR.MIDDLE, margin=.012)


def add_custom_slide(prs, title):
    """Add an editable continuation page matching the college's blue title band."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = WHITE
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  Inches(0), Inches(0), Inches(13.333), Inches(1.0))
    band.fill.solid(); band.fill.fore_color.rgb = RGBColor(80, 143, 214)
    band.line.fill.background()
    add_text(slide, .35, .08, 12.63, .82, title, size=25, color=INK,
             bold=True, font=FONT, align=PP_ALIGN.CENTER,
             valign=MSO_ANCHOR.MIDDLE, margin=.02)
    return slide


def fill_literature_continuations(prs):
    # These works carry forward topics and identifiable papers in Review II:
    # imbalance, interpretable ML, real-world fraud evaluation, and online detection.
    pages = [
        ("3. LITERATURE SURVEY (CONTINUED)", [
            ("SMOTE [8]", "Chawla et al. (2002)",
             "Introduced synthetic minority oversampling to improve learning from imbalanced classes.",
             "Resampling must be applied only within training folds; synthetic examples do not replace real fraud observations."),
            ("LIME [6]", "Ribeiro, Singh & Guestrin (2016)",
             "Explains an individual model prediction by fitting an interpretable approximation around that case.",
             "Explanations are local approximations and can vary with perturbations and settings."),
            ("SHAP [7]", "Lundberg & Lee (2017)",
             "Unifies additive feature-attribution methods using Shapley-value properties.",
             "Attributions describe model behavior; they do not establish causality or guarantee fast inference."),
        ]),
        ("3. LITERATURE SURVEY (CONTINUED)", [
            ("Realistic fraud modeling [9]", "Dal Pozzolo et al. (2018)",
             "Studies realistic modeling and learning strategies for credit-card fraud under class imbalance.",
             "Findings depend on the transaction stream and validation protocol; transfer to other domains must be tested."),
            ("SCARFF [10]", "Carcillo et al. (2018)",
             "Combines streaming infrastructure and machine learning for scalable near-real-time card fraud detection.",
             "A production streaming architecture is beyond this local dashboard prototype."),
            ("Sequence classification [11]", "Jurgovsky et al. (2018)",
             "Shows why transaction order and aggregated behavioral features can matter for card-fraud detection.",
             "Sequence methods require ordered customer histories; this project evaluates tabular benchmark pipelines."),
            ("Digital twin security survey [12]", "Jeremiah et al. (2024)",
             "Reviews digital-twin architectures, applications, security challenges, and open research directions.",
             "A cross-domain survey; it does not validate a digital twin for financial fraud."),
        ]),
    ]
    result = []
    for title, entries in pages:
        slide = add_custom_slide(prs, title)
        result.append(slide)
        if len(entries) == 4:
            for i, (name, author, finding, limit) in enumerate(entries):
                x = .70 + (i % 2) * 6.08
                y = 1.58 + (i // 2) * 2.55
                card(slide, x, y, 5.78, 2.22, name, f"{author}\nFinding: {finding}\nLimitation: {limit}",
                     color=[BLUE, TEAL, AMBER, CYAN][i], fill=PALE if i % 2 == 0 else WHITE,
                     title_size=14.2, body_size=12.0)
        else:
            for i, (name, author, finding, limit) in enumerate(entries):
                y = 1.48 + i * 1.72
                card(slide, .70, y, 11.95, 1.48, name, f"{author}\nFinding: {finding}\nLimitation: {limit}",
                     color=[BLUE, TEAL, AMBER][i], fill=PALE if i % 2 == 0 else WHITE,
                     title_size=15, body_size=12.2)
        footer(slide, "Survey notes are concise summaries of the cited papers; study results are not project results.", y=7.05)
    return result


REFERENCES = [
    "[1] R. J. Bolton and D. J. Hand, ‘Statistical Fraud Detection: A Review,’ Statistical Science, vol. 17, no. 3, pp. 235–249, 2002. doi:10.1214/ss/1042727940.",
    "[2] E. A. Lopez-Rojas, A. Elmir, and S. Axelsson, ‘PaySim: A Financial Mobile Money Simulator for Fraud Detection,’ Proc. 28th European Modeling and Simulation Symposium, 2016.",
    "[3] E. A. Lopez-Rojas and S. Axelsson, ‘BankSim: A Bank Payments Simulator for Fraud Detection Research,’ Proc. 26th European Modeling and Simulation Symposium, pp. 144–152, 2014.",
    "[4] T. Chen and C. Guestrin, ‘XGBoost: A Scalable Tree Boosting System,’ Proc. ACM SIGKDD, pp. 785–794, 2016. doi:10.1145/2939672.2939785.",
    "[5] F. T. Liu, K. M. Ting, and Z.-H. Zhou, ‘Isolation Forest,’ Proc. IEEE ICDM, pp. 413–422, 2008. doi:10.1109/ICDM.2008.17.",
    "[6] M. T. Ribeiro, S. Singh, and C. Guestrin, ‘“Why Should I Trust You?” Explaining the Predictions of Any Classifier,’ Proc. ACM SIGKDD, pp. 1135–1144, 2016. doi:10.1145/2939672.2939778.",
    "[7] S. M. Lundberg and S.-I. Lee, ‘A Unified Approach to Interpreting Model Predictions,’ Advances in Neural Information Processing Systems 30, 2017.",
    "[8] N. V. Chawla, K. W. Bowyer, L. O. Hall, and W. P. Kegelmeyer, ‘SMOTE: Synthetic Minority Over-sampling Technique,’ Journal of Artificial Intelligence Research, vol. 16, pp. 321–357, 2002. doi:10.1613/jair.953.",
    "[9] A. Dal Pozzolo, G. Boracchi, O. Caelen, C. Alippi, and G. Bontempi, ‘Credit Card Fraud Detection: A Realistic Modeling and a Novel Learning Strategy,’ IEEE Transactions on Neural Networks and Learning Systems, 2018. doi:10.1109/TNNLS.2017.2736643.",
    "[10] F. Carcillo, A. Dal Pozzolo, Y.-A. Le Borgne, O. Caelen, Y. Mazzer, and G. Bontempi, ‘SCARFF: A Scalable Framework for Streaming Credit Card Fraud Detection with Spark,’ Information Fusion, vol. 41, pp. 182–194, 2018. doi:10.1016/j.inffus.2017.09.005.",
    "[11] J. Jurgovsky et al., ‘Sequence Classification for Credit-card Fraud Detection,’ Expert Systems with Applications, vol. 100, pp. 234–245, 2018. doi:10.1016/j.eswa.2018.01.037.",
    "[12] S. R. Jeremiah, A. El Azzaoui, N. N. Xiong, and J. H. Park, ‘A Comprehensive Survey of Digital Twins: Applications, Technologies and Security Challenges,’ Journal of Systems Architecture, vol. 151, article 103120, 2024. doi:10.1016/j.sysarc.2024.103120.",
    "[13] I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, ‘Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization,’ Proc. ICISSP, pp. 108–116, 2018.",
    "[14] IEEE Computational Intelligence Society, ‘IEEE-CIS Fraud Detection,’ Kaggle competition dataset, 2019.",
]


def fill_references(prs):
    result = []
    for title, refs in [("REFERENCES", REFERENCES[:7]), ("REFERENCES (CONTINUED)", REFERENCES[7:])]:
        slide = add_custom_slide(prs, title)
        result.append(slide)
        add_paragraphs(slide, .76, 1.48, 11.8, 5.45, refs, size=12.3,
                       color=INK, gap=10, margins=(.08, .08, .06, .06))
    return result


def fill_research_gaps(prs):
    slide = prs.slides[5]
    add_slide_title(slide, "4. RESEARCH GAPS")
    gaps = [
        ("AI + digital twin integration", "Review II identifies detection and simulation as separate strands. This prototype combines them in one UI, but does not couple the simulator to learned model states."),
        ("Financial-domain twin evidence", "Digital-twin security literature largely studies cyber-physical/industrial settings; financial fraud use needs domain-specific validation."),
        ("Explainability", "Complex models need human-readable context. Current scoring shows simple risk factors; SHAP/LIME are not consistently integrated in the prediction flow."),
        ("Operational response time", "Offline benchmarks do not establish pre-authorization performance. The current form is manual and has no measured sub-second live feed."),
        ("Realistic, labeled data", "Public payment data are simulated or anonymized. Results cannot establish performance on a bank's private transaction stream."),
        ("False-positive burden", "Rare-event detection can achieve high recall while generating many false alerts; BankSim/IEEE precision demonstrates this trade-off."),
        ("Concept drift", "The saved models are static. Drift monitoring and adaptive retraining are not implemented."),
        ("Scalability and modularity", "The code is modular for a prototype, but no distributed streaming load test or production-scale study is provided."),
        ("XAI computation cost", "Explanation latency and stability have not been benchmarked; this matters before using local explanations in a live workflow."),
    ]
    for idx, (title, body) in enumerate(gaps):
        col, row = idx % 3, idx // 3
        card(slide, .45 + col * 4.28, 1.82 + row * 1.48, 4.02, 1.27,
             title, body, color=[BLUE, TEAL, AMBER, CYAN, RED, NAVY, GREEN, BLUE, TEAL][idx],
             fill=PALE if (idx + row) % 2 == 0 else WHITE, title_size=13.4, body_size=10.9)
    footer(slide, "These are the challenges motivating the Review-II objectives; current implementation status is shown on the next slides.")


def fill_objectives(prs):
    slide = prs.slides[6]
    add_slide_title(slide, "5. OBJECTIVES")
    goals = [
        ("01  Multi-Model ML Pipeline", "Compare LR, Random Forest, XGBoost, and Isolation Forest. Current build trains four model families; autoencoders are not included."),
        ("02  Digital Twin Scenarios", "Explore evolving risk states in a configurable simulator. It is a rule-based sandbox, not a calibrated live twin."),
        ("03  Explainable AI", "Show simple risk-factor context now; full SHAP/LIME integration across live prediction is future work."),
        ("04  Resilient Imbalance Handling", "Report rare-event metrics and use dataset-specific training strategies; resampling is not applied uniformly to all sources."),
        ("05  Low-Latency Monitoring", "Review-II target: sub-second monitoring. Current app scores manual inputs; live-feed latency is not measured."),
        ("06  Interactive Dashboard", "Implemented Streamlit navigation for data, evaluation, simulator, prediction, and executive insights."),
        ("07  Multi-Domain Validation", "Evaluate four datasets separately; do not interpret network intrusion results as financial-fraud results."),
        ("08  Drift Detection", "Review-II target: monitor changing fraud patterns. Drift alerting/adaptive retraining remains future work."),
    ]
    for i, (title, body) in enumerate(goals):
        col, row = i % 2, i // 2
        card(slide, .65 + col * 6.43, 1.82 + row * 1.24, 6.08, 1.08,
             title, body, color=BLUE if i % 2 == 0 else TEAL,
             fill=PALE_BLUE if i % 2 == 0 else PALE_GREEN,
             title_size=13.2, body_size=10.6)


def fill_research_work(prs):
    slide = prs.slides[7]
    add_slide_title(slide, "OBJECTIVE STATUS")
    shape = named(slide, "Content Placeholder 2")
    remove_shape(shape)
    add_text(slide, .65, 2.08, 12.5, .36, "REVIEW-II OBJECTIVES: PROJECT IMPLEMENTATION STATUS",
             size=13, color=MUTED, bold=True, align=PP_ALIGN.CENTER)
    status = [
        ("IMPLEMENTED", "Four datasets prepared\nFour model families per dataset\n16 saved evaluation pipelines\nFive Streamlit navigation pages"),
        ("PARTLY IMPLEMENTED", "Separate multi-domain evaluation\nRule-based twin-style simulator\nBasic prediction risk factors\nDataset-specific imbalance strategy"),
        ("NEXT WORK", "Integrated SHAP/LIME explanations\nConcept-drift monitoring\nLive transaction-stream latency\nIndependent temporal/external validation"),
    ]
    for i, (title, body) in enumerate(status):
        x = .65 + i * 4.27
        card(slide, x, 2.55, 3.95, 2.65, title, body,
             color=[GREEN, AMBER, BLUE][i], fill=[PALE_GREEN, PALE_AMBER, PALE_BLUE][i],
             title_size=15, body_size=13.2)
    add_text(slide, .92, 5.62, 12.0, .78,
             "Review-II proposed the broader targets; these status labels distinguish working project features from planned research extensions.",
             size=15, color=INK, align=PP_ALIGN.CENTER, fill=WHITE, margin=.13)


def fill_modules(prs):
    slide = prs.slides[8]
    add_slide_title(slide, "6. MODULE IDENTIFICATION")
    old = next((s for s in slide.shapes if s.name == "Content Placeholder 2"), None)
    if old:
        remove_shape(old)
    modules = [
        ("1. Data ingestion & validation", "download_datasets.py + modules/data_loader.py\nLoads the four local sources, checks target labels, and records rows and class counts."),
        ("2. Cleaning & preparation", "Dataset-specific pipelines\nHandle missing/infinite values, select inputs, split data, and fit transforms within training."),
        ("3. Imbalance strategy", "modules/model_trainer.py\nPaySim uses train-fold SMOTE-Tomek; BankSim/IEEE-CIS use class weighting; CICIDS is kept separate."),
        ("4. Feature engineering", "DomainFeatureExtractor + ColumnTransformer\nBuilds the configured features, encodes categories, and scales numeric inputs."),
        ("5. Multi-model trainer", "modules/model_trainer.py + offline_trainer.py\nFits Logistic Regression, Random Forest, XGBoost, and Isolation Forest."),
        ("6. Evaluation & persistence", "Holdout metrics + joblib artifacts\nStores precision/recall/F1/AUC, thresholds, confusion counts, dataset statistics, and pipelines."),
        ("7. Risk explanation", "app.py + modules/fraud_explainer.py\nPrediction shows simple risk-factor context; the optional SHAP/LIME utilities are not a full workflow."),
        ("8. Twin-style simulator & UI", "modules/digital_twin.py + app.py\nConfigured state transitions and heuristic intervention are presented alongside five dashboard pages."),
    ]
    for i, (title, body) in enumerate(modules):
        col, row = i % 2, i // 2
        card(slide, .65 + col * 6.43, 1.72 + row * 1.29, 6.08, 1.10,
             title, body, color=BLUE if col == 0 else TEAL,
             fill=WHITE if row % 2 else PALE, title_size=12.8, body_size=10.4)
    footer(slide, "Offline training is separate from Streamlit inference: offline_trainer.py writes artifacts; app.py loads and uses them.")


def fill_architecture(prs):
    slide = prs.slides[9]
    add_slide_title(slide, "7. SYSTEM ARCHITECTURE")
    old = next((s for s in slide.shapes if s.name == "Content Placeholder 2"), None)
    if old:
        remove_shape(old)
    boxes = [
        (.45, 2.05, 2.25, 1.38, "DATA SOURCES", "PaySim / BankSim\nIEEE-CIS / CICIDS2017", PALE_BLUE, BLUE),
        (2.95, 2.05, 2.25, 1.38, "LOAD & CLEAN", "Target checks / missing values\nDomain-specific inputs", PALE_GREEN, TEAL),
        (5.45, 2.05, 2.25, 1.38, "FEATURES & BALANCE", "Transforms / encodings\nSMOTE-Tomek: PaySim only", PALE_AMBER, AMBER),
        (7.95, 2.05, 2.25, 1.38, "TRAIN MODELS", "LR / Random Forest\nXGBoost / Isolation Forest", PALE_BLUE, BLUE),
        (10.45, 2.05, 2.25, 1.38, "EVALUATE & SAVE", "Holdout metrics + thresholds\nPipelines + dataset stats", PALE_GREEN, TEAL),
    ]
    for x, y, w, h, title, body, fill, color in boxes:
        rounded_box(slide, x, y, w, h, title, body, fill=fill, color=color,
                    title_size=12.5, body_size=10.5)
    for x in (2.72, 5.22, 7.72, 10.22):
        arrow(slide, x, 2.57, .18, .30)
    rounded_box(slide, .55, 4.30, 2.90, 1.48, "SAVED ARTIFACTS",
                "models/*.pkl\nevaluation_metrics.json\ndataset_stats.json",
                fill=PALE, color=NAVY, title_size=13, body_size=10.5)
    rounded_box(slide, 3.75, 4.30, 2.90, 1.48, "STREAMLIT DASHBOARD",
                "Data / Evaluation / Simulator\nPrediction / Executive Insights",
                fill=PALE_BLUE, color=BLUE, title_size=13, body_size=10.5)
    rounded_box(slide, 6.95, 4.30, 2.90, 1.48, "TWIN-STYLE SANDBOX",
                "Configured state transitions\nHeuristic intervention\nSeparate from model training",
                fill=PALE_AMBER, color=AMBER, title_size=13, body_size=10.5)
    rounded_box(slide, 10.15, 4.30, 2.63, 1.48, "ANALYST VIEW",
                "Metrics and plots\nManual example score\nScenario trajectory",
                fill=PALE_GREEN, color=TEAL, title_size=13, body_size=10.5)
    for x in (3.49, 6.69, 9.89):
        arrow(slide, x, 4.88, .20, .28)
    add_text(slide, .75, 6.03, 12.0, .42,
             "Technology: Python / pandas / NumPy / scikit-learn / imbalanced-learn / XGBoost / Streamlit / Plotly / joblib",
             size=12.5, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    footer(slide, "Prediction uses manual input; the simulator is not a live financial or network digital twin.")

def fill_development(prs):
    slide = prs.slides[10]
    add_slide_title(slide, "8. DEVELOPMENT & INTEGRATION")
    old = next((s for s in slide.shapes if s.name == "Content Placeholder 2"), None)
    if old:
        remove_shape(old)
    card(slide, .65, 1.95, 6.05, 2.0, "IMPLEMENTATION",
         "• Download/prepare data outside dashboard startup.\n"
         "• Split data before fitting model transforms.\n"
         "• Keep feature extraction and preprocessing in serialized pipelines.\n"
         "• Store metrics and dataset summaries as JSON for the UI.",
         color=BLUE, fill=PALE_BLUE, title_size=16, body_size=12.3)
    card(slide, 6.95, 1.95, 6.05, 2.0, "INTEGRATION",
         "offline_trainer.py → saved pipeline + JSON → app.py\n"
         "Live Prediction reuses the saved model pipeline and dataset/model threshold.\n"
         "Prediction forms align their fields to the model input schema.",
         color=TEAL, fill=PALE_GREEN, title_size=16, body_size=12.5)
    card(slide, .65, 4.24, 6.05, 1.85, "CHALLENGES ADDRESSED",
         "Target leakage checks • large-file bounded sampling • missing/infinite values • categorical encoding • class imbalance • time-aware splits for BankSim/IEEE when both classes permit.",
         color=AMBER, fill=PALE_AMBER, title_size=15, body_size=12.2)
    card(slide, 6.95, 4.24, 6.05, 1.85, "LIMITS TO VERIFY",
         "Input forms may impute unasked model fields. Thresholds need operational cost setting. Results need independent time-based validation. Scenario rules are illustrative, not learned.",
         color=RED, fill=WHITE, title_size=15, body_size=12.2)
    footer(slide, "Training/evaluation commands: `python offline_trainer.py`  |  Refresh saved-model metrics: `python offline_trainer.py --evaluate-existing`.")


def fill_prototype(prs):
    slide = prs.slides[11]
    add_slide_title(slide, "9. PROTOTYPE / FRAMEWORK")
    old = next((s for s in slide.shapes if s.name == "Content Placeholder 2"), None)
    if old:
        remove_shape(old)
    add_text(slide, .68, 1.86, 12.5, .45,
             "DASHBOARD WALKTHROUGH  |  streamlit run app.py", size=16,
             color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    navs = ["1  Data\nManagement", "2  Model\nEvaluation", "3  Twin\nSimulator",
            "4  Example\nPrediction", "5  Executive\nInsights"]
    colors = [BLUE, TEAL, AMBER, CYAN, NAVY]
    for i, (label, color) in enumerate(zip(navs, colors)):
        x = .65 + i * 2.57
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                    Inches(x), Inches(2.55), Inches(2.28), Inches(.9))
        sh.fill.solid(); sh.fill.fore_color.rgb = color
        sh.line.fill.background()
        add_text(slide, x + .05, 2.60, 2.18, .78, label, size=14,
                 color=WHITE, bold=True, align=PP_ALIGN.CENTER, margin=.01)
    # Prediction journey cards.
    stages = [
        ("SELECT", "Dataset +\nsaved model"),
        ("ENTER", "Example fields\n(manual input)"),
        ("SCORE", "Saved pipeline\nreturns model score"),
        ("DECIDE", "Compare score\nwith threshold"),
        ("EXPLAIN", "Display alert,\nmetrics and context"),
    ]
    for i, (title, body) in enumerate(stages):
        x = .73 + i * 2.57
        rounded_box(slide, x, 4.22, 2.13, 1.24, title, body,
                    fill=PALE if i % 2 == 0 else PALE_BLUE,
                    color=colors[i], title_size=13, body_size=11)
        if i < len(stages) - 1:
            arrow(slide, x + 2.20, 4.66, .25, .28)
    add_text(slide, 1.05, 5.88, 11.8, .75,
             "Prototype boundary: manual local scoring only. The scenario page uses configured transitions; neither feature is connected to a live payment or network feed.",
             size=14.5, color=INK, align=PP_ALIGN.CENTER, fill=PALE_AMBER, margin=.12)


def fill_conclusions(prs):
    slide = prs.slides[12]
    add_slide_title(slide, "PROJECT CONCLUSION")
    old = next((s for s in slide.shapes if s.name == "Content Placeholder 2"), None)
    if old:
        remove_shape(old)
    items = [
        ("A complete prototype workflow is present", "Four datasets, four model families, saved pipelines and metrics, and five dashboard sections are integrated."),
        ("Metrics reveal different operating trade-offs", "High recall can coexist with low precision; accuracy and AUC alone do not describe alert quality."),
        ("Results must stay in context", "BankSim and PaySim are simulated; CICIDS2017 is network intrusion; IEEE-CIS is an anonymized competition benchmark."),
        ("Validation remains essential", "Saved holdout values are not a production guarantee. The rule-based simulator is illustrative and separate from model training."),
    ]
    for i, (title, body) in enumerate(items):
        y = 1.98 + i * 1.17
        add_text(slide, .72, y, 3.1, .70, title, size=15, color=BLUE if i % 2 == 0 else TEAL,
                 bold=True, valign=MSO_ANCHOR.MIDDLE)
        add_text(slide, 3.75, y, 9.25, .76, body, size=15.3,
                 color=INK, valign=MSO_ANCHOR.MIDDLE)
        if i < len(items) - 1:
            line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                              Inches(.72), Inches(y + .92),
                                              Inches(12.95), Inches(y + .92))
            line.line.color.rgb = LINE; line.line.width = Pt(.8)
    add_text(slide, 1.0, 6.82, 12.0, .38,
             "Takeaway: a transparent detection prototype is useful when its data provenance, threshold trade-offs, and limitations are reported together.",
             size=13.5, color=NAVY, bold=True, align=PP_ALIGN.CENTER)


def fill_outcome(prs, metrics, stats):
    slide = prs.slides[13]
    add_slide_title(slide, "10. BEST MODEL SUMMARY")
    old = next((s for s in slide.shapes if s.name == "Content Placeholder 2"), None)
    if old:
        remove_shape(old)
    labels = [("paysim", "PaySim"), ("banksim", "BankSim"),
              ("cicids", "CICIDS2017"), ("ieee", "IEEE-CIS")]
    records = [metrics_row(metrics, stats, k, label) for k, label in labels]
    x, y, w, h = .55, 1.87, 12.9, 2.45
    table_shape = slide.shapes.add_table(5, 8, Inches(x), Inches(y), Inches(w), Inches(h))
    table = table_shape.table
    widths = [1.75, 2.20, 1.55, 1.55, 1.55, 1.20, 1.55, 1.55]
    for j, width in enumerate(widths):
        table.columns[j].width = Inches(width)
    headers = ["Dataset", "Best model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "Threshold"]
    for j, value in enumerate(headers):
        table.cell(0, j).text = value
    for i, rec in enumerate(records, start=1):
        values = [rec["dataset"], rec["best"], f'{rec["accuracy"]:.4f}',
                  f'{rec["precision"]:.4f}', f'{rec["recall"]:.4f}',
                  f'{rec["f1"]:.4f}', f'{rec["auc"]:.4f}', f'{rec["threshold"]:.3f}']
        for j, value in enumerate(values):
            table.cell(i, j).text = value
    for r, row in enumerate(table.rows):
        row.height = Inches(.49)
        for c, cell in enumerate(row.cells):
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(.04); cell.margin_right = Inches(.04)
            cell.margin_top = Inches(.025); cell.margin_bottom = Inches(.025)
            cell.fill.solid(); cell.fill.fore_color.rgb = NAVY if r == 0 else (PALE if r % 2 else WHITE)
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT if c < 2 else PP_ALIGN.CENTER
                p.space_after = Pt(0)
                for run in p.runs:
                    run.font.name = FONT; run.font.size = Pt(10.5 if r else 10.8)
                    run.font.bold = r == 0 or c == 0
                    run.font.color.rgb = WHITE if r == 0 else INK
    add_text(slide, .77, 4.50, 3.05, .38, "BEST-MODEL F1 BY DATASET", size=14,
             color=NAVY, bold=True, valign=MSO_ANCHOR.MIDDLE)
    for i, rec in enumerate(records):
        yy = 4.98 + i * .40
        add_text(slide, .80, yy, 1.45, .28, rec["dataset"], size=11.5,
                 color=INK, valign=MSO_ANCHOR.MIDDLE)
        bar_x, bar_w, max_w = 2.36, 3.75, 3.75
        bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                    Inches(bar_x), Inches(yy + .045), Inches(max_w), Inches(.20))
        bg.fill.solid(); bg.fill.fore_color.rgb = PALE_BLUE; bg.line.fill.background()
        fg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                    Inches(bar_x), Inches(yy + .045), Inches(max_w * rec["f1"]), Inches(.20))
        fg.fill.solid(); fg.fill.fore_color.rgb = [BLUE, TEAL, CYAN, AMBER][i]; fg.line.fill.background()
        add_text(slide, 6.20, yy, .64, .28, f'{rec["f1"]:.3f}', size=11.5,
                 color=NAVY, bold=True, valign=MSO_ANCHOR.MIDDLE)
    add_text(slide, 7.15, 4.62, 5.65, 1.80,
             "INTERPRETATION\nBankSim: recall 0.9386 but precision 0.1807 at threshold 0.50. Many alerts may be false alarms.\n\nPaySim: F1 0.8400 at threshold 0.005 on a rare-event sample.",
             size=13.1, color=INK, fill=PALE_AMBER, margin=.16)
    footer(slide,
           "Saved holdout results from models/evaluation_metrics.json. PaySim/CICIDS samples: 250,000 / 150,000; BankSim/IEEE-CIS: 594,643 / 590,540 rows.",
           y=6.95, size=8)


def fill_dataset_profile(prs, stats, slide=None):
    if slide is None:
        slide = add_custom_slide(prs, "10. DATASET PROFILE")
    rows = [
        ("PaySim — Mobile Money", "paysim", "Fraud cases", "Simulated mobile-money transactions; stratified sample used for training."),
        ("BankSim — Retail Banking", "banksim", "Fraud cases", "Simulated retail-bank transactions; entire available local file used."),
        ("CICIDS2017 — Network Traffic", "cicids", "Attack records", "Intrusion-detection task; this is not a financial-fraud dataset."),
        ("IEEE-CIS — E-commerce", "ieee", "Fraud cases", "Anonymized e-commerce competition data; entire available local file used."),
    ]
    for i, (title, key, positive_label, note) in enumerate(rows):
        rec = stats[key]
        col, row = i % 2, i // 2
        count = f'{rec["sampled_fraud_count"]:,}'
        ratio = f'{rec["sampled_fraud_ratio"]:.2%}'
        body = (f'Rows used: {rec["rows_used"]:,} / {rec["total_rows_available"]:,} available\n'
                f'{positive_label}: {count} ({ratio})  |  Source columns: {rec["total_features"]}\n{note}')
        card(slide, .68 + col * 6.25, 1.58 + row * 2.20, 5.92, 1.88,
             title, body, color=[BLUE, TEAL, AMBER, CYAN][i],
             fill=PALE_BLUE if i % 2 == 0 else WHITE,
             title_size=15, body_size=12.2)
    add_text(slide, .86, 6.25, 11.8, .50,
             "PaySim and CICIDS2017 are stratified samples; their card counts refer to the selected sample. Counts are from the saved dataset_stats.json.",
             size=11.7, color=MUTED, align=PP_ALIGN.CENTER)
    return slide


def fill_detailed_results(prs, metrics):
    specifications = [
        ("11. RESULTS: PaySim + BankSim", [("paysim", "PaySim"), ("banksim", "BankSim")],
         "BankSim recall is high, but its 0.1807 precision means many flagged cases are false alarms. PaySim uses a 0.005 threshold on the selected rare-event sample."),
        ("11. RESULTS: CICIDS2017 + IEEE-CIS", [("cicids", "CICIDS2017"), ("ieee", "IEEE-CIS")],
         "CICIDS2017 measures network attack detection, not payment fraud. IEEE-CIS Random Forest reaches 0.6828 recall at 0.1734 precision on its holdout split."),
    ]
    result_slides = []
    for title, datasets, note in specifications:
        slide = add_custom_slide(prs, title)
        result_slides.append(slide)
        records = []
        for key, label in datasets:
            for model_name, values in metrics[key]["results"].items():
                records.append((label, model_name, values))
        table_shape = slide.shapes.add_table(9, 8, Inches(.42), Inches(1.48), Inches(12.5), Inches(4.66))
        table = table_shape.table
        widths = [1.45, 2.05, 1.50, 1.50, 1.50, 1.50, 1.50, 1.50]
        for j, width in enumerate(widths):
            table.columns[j].width = Inches(width)
        headers = ["Dataset", "Model", "Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC", "Threshold"]
        for j, header in enumerate(headers):
            table.cell(0, j).text = header
        for i, (dataset, model_name, values) in enumerate(records, start=1):
            vals = [dataset, model_name, f'{values["Accuracy"]:.4f}', f'{values["Precision"]:.4f}',
                    f'{values["Recall"]:.4f}', f'{values["F1-Score"]:.4f}',
                    f'{values["ROC-AUC"]:.4f}', f'{values["Best_Threshold"]:.3f}']
            for j, value in enumerate(vals):
                table.cell(i, j).text = value
        for r, row in enumerate(table.rows):
            row.height = Inches(.50 if r else .54)
            for c, cell in enumerate(row.cells):
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.margin_left = Inches(.035); cell.margin_right = Inches(.035)
                cell.margin_top = Inches(.025); cell.margin_bottom = Inches(.025)
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(80, 143, 214) if r == 0 else (PALE_BLUE if r % 2 else WHITE)
                for paragraph in cell.text_frame.paragraphs:
                    paragraph.alignment = PP_ALIGN.LEFT if c < 2 else PP_ALIGN.CENTER
                    paragraph.space_after = Pt(0)
                    for run in paragraph.runs:
                        run.font.name = FONT
                        run.font.size = Pt(9.2 if r else 9.5)
                        run.font.bold = r == 0 or c == 0
                        run.font.color.rgb = WHITE if r == 0 else INK
        add_text(slide, .72, 6.36, 11.9, .43, note, size=11.5,
                 color=INK, align=PP_ALIGN.CENTER, fill=PALE_AMBER, margin=.08)
    return result_slides


def fill_timeline(prs):
    slide = prs.slides[14]
    add_slide_title(slide, "12. TIMELINE / GANTT CHART")
    old = named(slide, "TextBox 2")
    old.left, old.top = Inches(.65), Inches(1.72)
    old.width, old.height = Inches(12.5), Inches(.34)
    replace_text(old, "REVIEW-II PLAN (OCTOBER 2025?MARCH 2026)  |  Status updated from the current project files.",
                 size=13.5, color=MUTED, align=PP_ALIGN.CENTER,
                 valign=MSO_ANCHOR.MIDDLE, margins=(.05, .05, .02, .02))
    x0, y0 = 3.70, 2.12
    colw, rowh = 1.42, .57
    phases = ["Oct '25", "Nov '25", "Dec '25", "Jan '26", "Feb '26", "Mar '26"]
    for j, phase in enumerate(phases):
        add_text(slide, x0 + j * colw, y0, colw - .06, .42, phase,
                 size=11.2, color=NAVY, bold=True, align=PP_ALIGN.CENTER)
    tasks = [
        ("Problem identification + literature review", 0, 1, "DONE", GREEN),
        ("Dataset collection and source checks", 1, 1, "DONE", GREEN),
        ("Preprocessing and exploratory analysis", 2, 1, "DONE", GREEN),
        ("Model development and evaluation", 3, 1, "DONE", GREEN),
        ("Scenario simulator + XAI integration", 4, 1, "PARTIAL", AMBER),
        ("Dashboard + live transaction integration", 5, 1, "PARTIAL", AMBER),
    ]
    for i, (task, start, span, status, color) in enumerate(tasks):
        yy = y0 + .57 + i * rowh
        add_text(slide, .65, yy, 2.92, .44, task, size=11.2, color=INK,
                 valign=MSO_ANCHOR.MIDDLE)
        for j in range(6):
            cell = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                          Inches(x0 + j * colw + .05), Inches(yy + .08),
                                          Inches(colw - .16), Inches(.27))
            cell.fill.solid(); cell.fill.fore_color.rgb = PALE
            cell.line.color.rgb = LINE; cell.line.width = Pt(.5)
        bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                     Inches(x0 + start * colw + .05), Inches(yy + .08),
                                     Inches(span * colw - .16), Inches(.27))
        bar.fill.solid(); bar.fill.fore_color.rgb = color; bar.line.fill.background()
        add_text(slide, 12.12, yy, 1.15, .44, status, size=9.8,
                 color=color, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, .90, 6.63, 12.0, .42,
             "Next milestones: external/time-based validation, integrated explanation checks, drift monitoring, and measured live-feed latency.",
             size=12.4, color=NAVY, bold=True, align=PP_ALIGN.CENTER)

def fill_thank_you(prs):
    slide = prs.slides[15]
    title = named(slide, "Title 1")
    replace_text(title, "Thank You", size=38, color=NAVY, bold=True,
                 align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE,
                 margins=(.1, .1, .1, .1))
    add_text(slide, 1.6, 4.55, 10.8, .72,
             "QUESTIONS & DISCUSSION\nNexus Fraud Defense  |  Shambhu Pandey  |  25MCA1020",
             size=18, color=INK, align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE)


def main():
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"College template not found: {TEMPLATE}")
    with METRICS_PATH.open(encoding="utf-8") as f:
        metrics = json.load(f)
    with STATS_PATH.open(encoding="utf-8") as f:
        stats = json.load(f)
    prs = Presentation(str(TEMPLATE))
    if len(prs.slides) != 16:
        raise ValueError(f"Expected 16 template slides, found {len(prs.slides)}")

    fill_cover(prs)
    fill_contents(prs)
    fill_abstract(prs)
    fill_introduction(prs)
    fill_literature(prs)
    fill_research_gaps(prs)
    fill_objectives(prs)
    fill_research_work(prs)
    fill_modules(prs)
    fill_architecture(prs)
    fill_development(prs)
    fill_prototype(prs)
    fill_conclusions(prs)
    fill_outcome(prs, metrics, stats)
    fill_timeline(prs)
    fill_thank_you(prs)
    base_slides = list(prs.slides)

    # Add continuation pages, then place them beside the sections they extend.
    lit_pages = fill_literature_continuations(prs)
    ref_pages = fill_references(prs)
    profile_page = fill_dataset_profile(prs, stats)
    result_pages = fill_detailed_results(prs, metrics)

    def slide_id_for(slide):
        for item in prs.slides._sldIdLst:
            rid = item.rId
            if prs.part.related_part(rid) == slide.part:
                return item
        raise ValueError("Could not locate slide in presentation order")

    slide_ids = prs.slides._sldIdLst
    moved = [slide_id_for(s) for s in lit_pages + [profile_page] + result_pages + ref_pages]
    lit_items = moved[:2]
    result_items = moved[2:5]
    ref_items = moved[5:]
    for item in moved:
        slide_ids.remove(item)
    # Literature pages follow the original literature slide (index 4).
    for offset, item in enumerate(lit_items):
        slide_ids.insert(5 + offset, item)

    # Latest dataset profile and detailed model results follow the outcome summary.
    timeline_item = slide_id_for(base_slides[14])
    result_position = list(slide_ids).index(timeline_item)
    for offset, item in enumerate(result_items):
        slide_ids.insert(result_position + offset, item)

    # References appear after the dated project plan and before Thank You.
    thank_you_item = slide_id_for(base_slides[15])
    ref_position = list(slide_ids).index(thank_you_item)
    for offset, item in enumerate(ref_items):
        slide_ids.insert(ref_position + offset, item)

    # Keep the template's printed page numbers aligned after inserting four pages.
    for page_number, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if not getattr(shape, "has_text_frame", False):
                continue
            if shape.text.strip().isdigit():
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        run.text = str(page_number)
        if slide in lit_pages or slide in ref_pages or slide is profile_page or slide in result_pages:
            add_text(slide, 12.45, 7.02, .40, .22, str(page_number),
                     size=9, color=MUTED, align=PP_ALIGN.RIGHT,
                     valign=MSO_ANCHOR.MIDDLE, margin=.01)

    prs.save(str(OUTPUT))
    print(f"Created: {OUTPUT}")
    print(f"Slides: {len(prs.slides)}")
    print(f"Size: {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
