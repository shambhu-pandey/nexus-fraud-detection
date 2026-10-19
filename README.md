# Nexus Fraud Defense

**A dashboard for comparing fraud and intrusion detection models, exploring risk scenarios, and scoring example transactions.**

This README is both a project guide and a presentation aid. It describes the implementation in this repository and the currently saved evaluation results. Model scores can change when you retrain the models, change the data, or change a decision threshold.

## Project in one minute

Nexus Fraud Defense is a Python and Streamlit prototype for studying how machine learning can flag suspicious activity. It brings together four labeled datasets from different domains, prepares their features, trains four model types, and shows evaluation results in a dashboard. A user can also enter an example record for scoring and explore configured what-if scenarios in a digital-twin-style simulator.

The project is a research and demonstration tool. It does not connect to payment networks, banks, or live security infrastructure, and it does not block real transactions. Its “live prediction” page scores a record entered in the dashboard using a locally saved model.

### Short panel introduction

> “My project, Nexus Fraud Defense, is an interactive framework for comparing machine-learning approaches to fraud and intrusion detection. It uses PaySim and BankSim payment benchmarks, IEEE-CIS e-commerce data, and CICIDS2017 network traffic. The dashboard covers data and evaluation, example prediction, scenario simulation, and executive summaries. The results are benchmark holdout results; the simulator uses configured transition probabilities and is intended for scenario exploration.”

## Problem and objective

Fraud and intrusion examples are often rare compared with normal activity. A model can therefore report high accuracy while still missing suspicious cases. The project makes the trade-offs visible through precision, recall, F1-score, ROC-AUC, confusion matrices, and configurable decision thresholds, alongside accuracy.

The objective is to build an understandable, reproducible prototype that:

- prepares several labeled datasets for model training;
- compares supervised classifiers with an unsupervised anomaly detector;
- makes saved holdout metrics and thresholds visible;
- scores user-entered examples with a saved pipeline; and
- illustrates possible risk and mitigation scenarios in a dashboard.

## How the application works

1. **Load a dataset.** The data loader reads the selected local dataset and its target label. PaySim and CICIDS2017 are sampled to configured limits; BankSim and IEEE-CIS use their full labeled files when present.
2. **Choose inputs and prepare features.** Dataset-specific feature lists are defined in `config.py`. Known target-leakage fields are excluded. The model pipeline handles categorical and numeric columns, including encoding and scaling where appropriate.
3. **Create a holdout.** The normal split is 80% training and 20% testing. BankSim and IEEE-CIS use time-ordered splits when the time field allows both splits to retain both classes; the other datasets use stratified random splits. The test portion is held out from model fitting.
4. **Train and evaluate.** Four pipelines are evaluated: Logistic Regression, Random Forest, XGBoost, and Isolation Forest. The first three are supervised classifiers. Isolation Forest is an unsupervised anomaly detector; it is not directly equivalent to the classifiers.
5. **Save artifacts.** Trained models, evaluation metrics, dataset statistics, and feature names are stored under `models/`. The dashboard reads these saved artifacts; retraining is a separate offline command.
6. **Explore results and examples.** The dashboard presents dataset summaries, metrics, predictions, and scenario outputs. Prediction results depend on the selected dataset, saved model, and threshold.

### What “digital twin” means in this prototype

The simulator represents a configurable state-transition scenario and compares possible trajectories or mitigation settings. It is **not** a model learned from the selected dataset, a live copy of a bank or network, or a trained reinforcement-learning agent. Present it as a what-if simulation component of the framework.

## Dashboard walkthrough

The left navigation contains five sections. A good demo order is 1 → 2 → 4 → 3 → 5.

| Section | What it shows | What to explain |
|---|---|---|
| **1. Data Management** | Dataset descriptions, available local data/model status, and dataset summaries | Explain the four data domains and that the source files are local benchmark data. |
| **2. Model Evaluation** | Saved per-model metrics, thresholds, confusion/evaluation views, and the selected best model | Explain why recall, precision, and F1 matter when fraud is rare. “Best” is selected by F1 among the supervised models. |
| **3. Digital Twin Simulator** | Configurable risk-state scenarios and mitigation comparisons | Explain that transitions are configured for scenario analysis; they are not learned from transaction records. |
| **4. Live Prediction** | Input forms and a risk prediction from a saved model | Describe this as interactive example scoring, not a live financial transaction decision. |
| **5. Executive Insights** | A summary view of the saved project metrics and model results | Use it to close with the key results, caveats, and next steps. |

## Datasets

The dashboard combines related but different tasks. CICIDS2017 detects network attacks, while the other datasets concern payment or e-commerce fraud. Their scores should not be compared as if they came from one common test set.

| Dataset | Domain and target | Rows used in the saved results | Important context |
|---|---|---:|---|
| **PaySim** | Simulated mobile money; `isFraud` | 250,000 sampled from 6,362,620 | Synthetic benchmark modeled on mobile-money activity. The sampled fraud ratio is about 0.129%. |
| **BankSim** | Simulated retail payments; `fraud` | 594,643 | A payment simulator dataset, not actual bank customer records. The saved data has 7,200 fraud rows (about 1.21%). |
| **CICIDS2017** | Network intrusion; `Label` | 150,000 sampled from 2,830,743 | Network-security task, not payment fraud. The sampled attack ratio is about 19.70%. |
| **IEEE-CIS** | E-commerce transactions; `isFraud` | 590,540 | Labeled Vesta/IEEE-CIS benchmark training records. The configured model uses 98 input features; the saved data has 20,663 fraud rows (about 3.50%). |

The application expects the full compressed data sources described in [`data/DATA_SOURCES.md`](data/DATA_SOURCES.md). Small CSV preview files are for inspection and do not represent the complete training data. BankSim is synthetic by design; PaySim is also simulated. The IEEE-CIS records are anonymized competition data, not an ongoing live feed.

## Models and evaluation

| Model | Role in this project |
|---|---|
| **Logistic Regression** | Supervised linear classification baseline. |
| **Random Forest** | Supervised ensemble of decision trees. |
| **XGBoost** | Supervised gradient-boosted trees. |
| **Isolation Forest** | Unsupervised anomaly detection. Its output is converted to predictions for display, so interpret its precision/recall and threshold in that context. |

### Metrics in plain language

- **Accuracy:** share of all records classified correctly. With rare fraud, a model can get high accuracy by mostly predicting the majority class.
- **Precision:** of the records flagged, how many were actually positive. Higher precision means fewer false alarms.
- **Recall:** of all positive cases, how many the model found. Higher recall means fewer missed cases.
- **F1-score:** one balance of precision and recall; it falls when either one is low.
- **ROC-AUC:** how well scores rank positive records above negative records across thresholds. It does not specify a useful operating threshold on its own.
- **Threshold:** probability cutoff used to turn a model score into a positive/negative decision. Lowering it often finds more positives but can increase false alarms.

### Currently saved holdout results

These values are read from `models/evaluation_metrics.json` and `models/dataset_stats.json` in this project copy. Each row shows the saved model selected as best by F1 among the supervised classifiers. They are benchmark results on the configured holdout split, not a guarantee of future or production performance.

| Dataset | Best by F1 | Accuracy | Precision | Recall | F1-score | ROC-AUC | Threshold |
|---|---|---:|---:|---:|---:|---:|---:|
| PaySim | XGBoost | 0.9995 | 0.7326 | 0.9844 | 0.8400 | 0.9935 | 0.005 |
| BankSim | Random Forest | 0.9534 | 0.1807 | 0.9386 | 0.3031 | 0.9920 | 0.500 |
| CICIDS2017 | XGBoost | 0.8781 | 0.6179 | 0.9992 | 0.7636 | 0.9989 | 0.005 |
| IEEE-CIS | Random Forest | 0.8771 | 0.1734 | 0.6828 | 0.2766 | 0.8684 | 0.500 |

For example, BankSim accuracy is 95.34%, but precision is 18.07%. In this saved evaluation, that means the model catches many positive cases (recall 93.86%) while also flagging many non-fraud cases. This is why accuracy alone is not a sufficient summary. The chosen threshold expresses a trade-off, not a universal best setting.

## Installation and running

Python 3.10–3.12 is recommended. Model training needs several GB of memory; more is helpful.

### 1. Create an environment and install packages

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell prevents activation, run commands through `.venv\Scripts\python.exe` directly.

### 2. Prepare the datasets

```powershell
python .\download_datasets.py
```

See [`data/DATA_SOURCES.md`](data/DATA_SOURCES.md) for source details and access notes. The dataset downloader prepares local files; IEEE-CIS may require the project’s configured OpenML conversion dependencies and the applicable competition data terms. `generate_datasets.py` creates small synthetic demo examples for BankSim/IEEE; it does not reproduce the original benchmark datasets.

### 3. Start the dashboard

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit, normally `http://localhost:8501`. The dashboard uses saved models and metrics under `models/`. If those artifacts are missing or stale, train them before the presentation.

### 4. Train or refresh saved model artifacts

Train all configured datasets:

```powershell
python .\offline_trainer.py
```

Train selected dataset keys only:

```powershell
python .\offline_trainer.py --datasets banksim,ieee
```

Recompute evaluation metrics using existing saved models, without retraining:

```powershell
python .\offline_trainer.py --evaluate-existing
```

Dataset keys are `paysim`, `banksim`, `cicids`, and `ieee`. The trainer skips datasets whose required source files are missing. Training can take several minutes or longer depending on hardware and selected datasets. For the currently saved dataset sizes and download behavior, see [`INSTALLATION.md`](INSTALLATION.md).

## Suggested presentation plan

An 8-slide presentation can follow this sequence:

1. **Title and motivation:** Nexus Fraud Defense and why fraud detection matters.
2. **Problem:** rare positive cases make accuracy alone misleading.
3. **Objectives and scope:** compare models and provide a usable demonstration; clarify that this is a prototype.
4. **Datasets:** introduce PaySim, BankSim, IEEE-CIS, and CICIDS2017, including which are simulated and which task is network security.
5. **Method:** feature selection, leakage exclusions, preprocessing, holdout strategy, model families, and thresholds.
6. **Results:** present the saved metrics table; discuss precision/recall trade-offs and avoid claiming perfect prediction.
7. **Dashboard demo:** show evaluation, one example prediction, and one simulator scenario.
8. **Limitations and next steps:** validate on new data, assess operational costs and fairness, tune thresholds for a defined use case, and integrate only with an authorized test environment.

### A short results explanation

“The saved metrics show different behavior across datasets. PaySim has a high F1-score at a low threshold, while BankSim and IEEE-CIS have much lower precision at their saved operating points. That means many flagged records may be false alarms. I report precision and recall with accuracy so that the trade-off remains visible. The results are holdout benchmark evaluations and need external validation before any operational use.”

## Questions a panel may ask

**Why not report accuracy only?**

Fraud is a minority class in several datasets. A high accuracy value can hide missed fraud, so precision, recall, F1, and confusion counts provide more useful context.

**Why are there four different datasets?**

They let the prototype demonstrate related detection methods across payment fraud, e-commerce fraud, and network intrusion. They are separate tasks, so their metrics are not a direct head-to-head comparison.

**Why do thresholds differ?**

Thresholds control the balance between false alarms and missed cases. This project stores dataset/model-specific thresholds; a real deployment would need a threshold chosen for its own cost, review capacity, and risk tolerance.

**Is the digital twin trained from the data?**

No. The current simulator uses configured state-transition probabilities for scenario exploration. It is not trained from the benchmark records and is not a reinforcement-learning policy.

**Does “Live Prediction” score real transactions?**

No. It scores inputs entered in the dashboard with a locally saved model. It is not connected to a payment or security network.

**Can these numbers be guaranteed in production?**

No. They are results for saved benchmark holdout splits. Performance can change on new populations, time periods, or operating conditions and needs independent validation.

## Project file map

| File or folder | Purpose |
|---|---|
| `app.py` | Streamlit dashboard, navigation, and page rendering. |
| `config.py` | Dataset definitions, feature lists, model settings, thresholds, and example inputs. |
| `modules/data_loader.py` | Dataset loading, target/feature preparation, split creation, and dataset statistics. |
| `modules/model_trainer.py` | Preprocessing and model pipelines, training/evaluation, saved model loading, and prediction helpers. |
| `modules/digital_twin.py` | Configured scenario-transition and mitigation simulation. |
| `modules/explainability.py` | Prediction explanation and feature-importance helpers used by the app. |
| `offline_trainer.py` | Command-line workflow for training models or refreshing saved metrics. |
| `download_datasets.py` | Downloads/prepares dataset files for local use. |
| `data/` | Local datasets, previews, source notes, and download artifacts. |
| `models/` | Saved model pipelines, evaluation metrics, and dataset statistics. |
| `INSTALLATION.md` | Setup, dataset preparation, and run instructions. |
| `DEVELOPMENT.md` | Developer notes and project workflow. |
| `generate_project_ppt.py` | Script for generating a starter project presentation deck. |

## Limitations and responsible interpretation

- Benchmark performance is not a production guarantee; external and time-based validation is needed.
- PaySim and BankSim are simulated datasets. IEEE-CIS is anonymized competition data. CICIDS2017 is a network intrusion dataset and represents a different detection task.
- Rare-event detection requires considering false alarms, missed cases, class balance, and the costs of each outcome.
- The prototype does not connect to financial institutions or block transactions.
- The scenario simulator uses configured transitions rather than learned system behavior.
- Dataset use is subject to source licenses and access terms. Review [`data/DATA_SOURCES.md`](data/DATA_SOURCES.md) before redistribution.

## Further reading

- [Installation and run guide](INSTALLATION.md)
- [Dataset sources and status](data/DATA_SOURCES.md)
- [Development notes](DEVELOPMENT.md)
- [Presentation generation notes](README_generate_ppt.md)
