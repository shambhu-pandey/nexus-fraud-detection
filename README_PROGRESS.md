# Nexus Fraud Defense — Full Project Guide

This document is a detailed, plain-language guide to the project. It is written for a student who needs to understand the code, explain it to a panel, demonstrate the dashboard, and describe what remains to improve. It reflects the source code and saved artifacts currently in this repository. If you retrain the models or change datasets/configuration, refresh the results in this guide from the newly saved files.

For a shorter overview and quick start, see [`README.md`](README.md). For machine setup, see [`INSTALLATION.md`](INSTALLATION.md). Dataset source and access notes are in [`data/DATA_SOURCES.md`](data/DATA_SOURCES.md).

## 1. Project identity

**Project name:** Nexus Fraud Defense  
**Project description:** Digital Twin-Enabled Framework for Forecasting and Mitigating Fraud  
**Application:** Python dashboard built with Streamlit  
**Main purpose:** Demonstrate model training and evaluation, interactive example scoring, and risk-scenario simulation across several labeled datasets.

### One-sentence explanation

Nexus Fraud Defense is a research prototype that prepares four benchmark datasets, compares fraud or intrusion detection models, and presents their metrics and example predictions in an interactive dashboard.

### What problem does it address?

Fraud and cyber-attacks can be difficult to detect because positive examples are often uncommon, patterns can differ by domain, and an alert has costs. A detection system needs to balance two kinds of errors:

- **False negative:** a real fraud/attack is missed.
- **False positive:** a legitimate transaction or normal network flow is flagged.

The project makes these trade-offs visible using precision, recall, F1-score, confusion matrix counts, and thresholds, in addition to accuracy. It provides a single interface for inspecting different datasets and model results.

### What the project does not do

This code is a demonstration and research framework. It does not connect to banks, card networks, mobile-money providers, merchants, or live network monitoring. It does not stop, approve, or block actual transactions. The page named **Live Prediction** scores a manually entered example using a saved model; it is not a production live feed.

## 2. Goals and scope

The project aims to:

1. Load labeled data from multiple detection domains.
2. Select useful input columns and remove target/leakage fields.
3. Create repeatable training and holdout data splits.
4. Train multiple model types through a consistent preprocessing pipeline.
5. Compare performance with metrics appropriate for class imbalance.
6. Save the trained pipelines and their supporting metrics locally.
7. Provide a dashboard for data status, evaluation, manual example scoring, simulations, and summaries.

The project currently combines financial fraud data and network intrusion data to demonstrate a reusable detection workflow. These tasks are related in their use of binary classification, but the datasets, labels, features, and meaning of a positive prediction differ. Their scores are not direct head-to-head comparisons.

## 3. Application architecture

The major parts connect as follows:

```text
Dataset files
    │
    ▼
modules/data_loader.py ── loads labels, chooses features, splits train/test
    │
    ▼
modules/model_trainer.py ── preprocessing + model pipelines + holdout metrics
    │
    ├── saved pipelines: models/best_<dataset>_<model>.pkl
    ├── metrics:         models/evaluation_metrics.json
    └── data stats:      models/dataset_stats.json
              │
              ▼
           app.py ── five Streamlit sections read saved results and models
              │
              ├── modules/digital_twin.py (configured scenario simulation)
              └── modules/fraud_explainer.py / explainability helpers
```

### Main files

| File | Responsibility |
|---|---|
| `app.py` | Defines Streamlit layout, navigation, forms, charts, and the five dashboard sections. |
| `config.py` | Defines dataset paths, labels, domain descriptions, feature lists, sample limits, model settings, thresholds, and example inputs. |
| `modules/data_loader.py` | Resolves dataset files, reads full/large CSV files, binarizes labels, selects features, and creates train/test splits. |
| `modules/model_trainer.py` | Builds preprocessing/model pipelines, trains the four model types, evaluates results, loads thresholds, scores examples, and saves/loads pipelines. |
| `modules/digital_twin.py` | Runs stochastic state trajectories using per-domain transition matrices and a simple configured intervention rule. |
| `modules/explainability.py` | Provides SHAP/LIME and feature-importance helper functions. Availability of a helper does not mean every dashboard result uses a full SHAP or LIME explanation. |
| `modules/fraud_explainer.py` | Provides the simplified explanation displayed after the example prediction. |
| `offline_trainer.py` | Command-line entry point to train models or recompute metrics with saved models. |
| `download_datasets.py` | Downloads/prepares full data sources and creates small inspection previews. |
| `generate_datasets.py` | Generates synthetic demo examples; these are not the original BankSim or IEEE-CIS benchmark files. |
| `data/DATA_SOURCES.md` | Records dataset provenance, source links, and access notes. |
| `models/` | Stores trained model artifacts and metrics/statistics JSON and CSV files. |

## 4. The complete data-to-prediction flow

### Step 1: Find and read local data

The downloader prepares files under `data/`. `config.py` maps each dataset key to a primary file path, alternate paths, expected label, sample cap, and domain metadata. The loader uses an available configured file and raises a useful error if no usable file or target column is found.

Small files such as `paysim.csv`, `banksim.csv`, `cicids.csv`, and `ieee.csv` are inspection previews. The training workflow uses the full compressed dataset files when they are present. This is why the preview row count can be much smaller than the number of rows used for training.

For large files, the loader reads chunks and maintains a bounded, reproducible class-aware sample. PaySim and CICIDS2017 use configured maximum sample sizes. BankSim and IEEE-CIS are below their configured caps in this project and are used in full. The saved dataset statistics record the available row count, number of rows used, positive count, positive ratio, whether sampling occurred, and the source path.

### Step 2: Identify and standardize the target

The expected targets are:

| Dataset | Source target | Meaning of positive class in this application |
|---|---|---|
| PaySim | `isFraud` | Fraud transaction. |
| BankSim | `fraud` | Fraud transaction. |
| CICIDS2017 | `Label` | Any label other than `BENIGN` is grouped as an attack. The original attack categories are collapsed into one positive class. |
| IEEE-CIS | `isFraud` | Fraud transaction. |

The loader standardizes labels to a binary `fraud` target: zero for the negative class and one for a positive case. For a text label, CICIDS2017's `BENIGN` value becomes zero and other labels become one. The target is split away from the features before model training.

### Step 3: Select allowed features and prevent target leakage

The selected raw inputs are declared in `RAW_FEATURES_BY_DATASET` in `config.py`:

| Dataset | Selected input fields |
|---|---|
| PaySim | `type`, `amount`, `oldbalanceOrg`, `oldbalanceDest` |
| BankSim | `step`, `age`, `gender`, `category`, `amount` |
| CICIDS2017 | `Destination Port`, `Flow Duration`, `Total Fwd Packets`, `Total Backward Packets`, `SYN Flag Count`, `Packet Length Mean`, `Average Packet Size` |
| IEEE-CIS | Transaction/time, card, product, email, device and distance fields, plus the configured `C`, `D`, `M`, and `V` fields (98 inputs total). |

Target variants such as `fraud`, `isFraud`, `Label`, and `Class` are defensively removed from the feature matrix. The project also lists balance-result fields such as `newbalanceOrig`, `newbalanceDest`, and simulator flags such as `isFlaggedFraud` as leakage-prone columns. The model pipeline asserts that the target is not in the model input.

The intent is that the classifier sees the selected inputs and learns an association with the label, rather than receiving the answer itself. Feature selection still requires domain review: a column can be leakage-prone even when it is not literally named like the target.

### Step 4: Split training and holdout data

The configured test size is 20% and the random seed is 42. For PaySim and CICIDS2017, the split is stratified and randomized so the positive/negative proportions are represented in both partitions. For BankSim and IEEE-CIS, the loader sorts by `step` or `TransactionDT` and attempts a chronological split when both partitions retain both classes. If that condition is not met, it falls back to a stratified random split.

Preprocessors and classifiers are fitted on training data. The holdout data is passed through the fitted model pipeline to calculate results. The holdout is not used to fit encoders or scalers. The saved BankSim/IEEE statistics reflect all labeled rows before the split; the holdout portion is part of those rows, not additional data.

### Step 5: Transform features inside the model pipeline

The model pipeline contains a domain feature extractor and a column-based preprocessor. Depending on the selected inputs, it:

- converts infinite values and missing values into safe values;
- fills categorical missing values with a marker;
- derives features such as time-of-day flags and selected transaction ratios;
- applies a log transform to amount-like columns;
- one-hot encodes configured categorical fields;
- standardizes numeric values; and
- preserves the feature order expected by a saved model.

The same serialized pipeline is used for manual scoring, which avoids needing to recreate preprocessing separately at prediction time. It also means the input form may ask for fewer fields than the training file contains; remaining model inputs are filled/aligned by the prediction helper. This behavior is convenient for a demo, but those neutral defaults can make a manually entered prediction less representative than a complete record.

### Step 6: Train models

`offline_trainer.py` calls the data loader and then trains the four configured models per selected dataset. Each model is saved as a `joblib` pipeline in `models/`.

| Model | Learning style | How to explain it |
|---|---|---|
| Logistic Regression | Supervised | A linear baseline that estimates the relationship between input features and the binary label. |
| Random Forest | Supervised | An ensemble of decision trees whose combined predictions can capture nonlinear patterns. |
| XGBoost | Supervised | A boosted-tree model that builds trees sequentially to reduce earlier errors. |
| Isolation Forest | Unsupervised anomaly detection | Learns unusual patterns without using labels during its fit. Labels are used later to compare anomaly flags with known outcomes. |

The training setup includes class-imbalance handling. In the current code, BankSim and IEEE-CIS supervised classifiers use class weights; XGBoost uses a positive-class weight there. The pipeline's SMOTETomek branch is enabled for datasets other than CICIDS, BankSim, and IEEE-CIS, which means it applies to PaySim among the configured keys. Isolation Forest is fitted without labels.

The training routine picks the model with the highest saved F1-score among the supervised models, using recall as a tie-breaker. Isolation Forest remains in the comparison table but is excluded from the primary “best model” choice when supervised results exist.

### Step 7: Calculate and store evaluation results

The evaluation function applies the configured threshold and saves:

- accuracy and balanced accuracy;
- precision, recall, and F1-score;
- PR-AUC and ROC-AUC;
- the decision threshold;
- confusion matrix counts (`TP`, `TN`, `FP`, `FN`); and
- downsampled ROC curve coordinates for charting.

Threshold selection is supplied by dataset/model settings or `models/thresholds_selected.json`; evaluation code explicitly avoids tuning a threshold against the holdout itself. The UI's global fallback is 0.25, but the saved dataset/model threshold is preferred when it exists. A displayed threshold is a decision setting, not a property that makes one model universally correct.

Isolation Forest does not provide a probability in the same sense as the supervised classifiers. Its anomaly decision is evaluated as an outlier flag. The UI converts a decision score to a display score for some uses, so treat its “probability” as a relative/demo score, not a calibrated probability of fraud.

## 5. Datasets and provenance

### PaySim

- **Domain:** synthetic mobile-money transactions.
- **Target:** `isFraud`.
- **Rows available in saved statistics:** 6,362,620.
- **Rows used:** 250,000 in the saved training/evaluation run.
- **Positive cases in used sample:** 322 (0.1288%).
- **Model inputs:** transaction type, amount, and two old-balance fields.
- **Interpretation:** simulated data inspired by mobile-money activity; it is not a log of observed customer transactions.

### BankSim

- **Domain:** simulated retail-payment transactions.
- **Target:** `fraud`.
- **Rows available and used:** 594,643.
- **Positive cases:** 7,200 (1.2108%).
- **Model inputs:** simulation step, age, gender, category, and amount.
- **Interpretation:** BankSim is synthetic by design. Describe it as published simulator data, not actual customer bank records.

### CICIDS2017

- **Domain:** network traffic and intrusion detection.
- **Target:** `Label`, mapped to benign versus attack.
- **Rows available in saved statistics:** 2,830,743.
- **Rows used:** 150,000.
- **Positive cases in used sample:** 29,549 (19.6993%).
- **Model inputs:** selected flow and packet statistics.
- **Interpretation:** this is a cybersecurity task, not a payment-fraud dataset. The source labels are reduced to one attack class in the project.

### IEEE-CIS

- **Domain:** anonymized e-commerce transactions from the IEEE-CIS/Vesta benchmark.
- **Target:** `isFraud`.
- **Rows available and used:** 590,540 labeled records.
- **Positive cases:** 20,663 (3.4990%).
- **Model inputs:** 98 configured transaction, card, email/device and anonymized feature fields.
- **Interpretation:** competition benchmark data, not a current live transaction stream. The source's access terms apply.

More source information and citations are maintained in [`data/DATA_SOURCES.md`](data/DATA_SOURCES.md). The downloader keeps full data in compressed files and creates 5,000-row CSV previews for convenient inspection. Demo CSVs made by `generate_datasets.py` should not be substituted for the original benchmark files when reproducing the saved benchmark results.

## 6. Understanding the dashboard, page by page

### Page 1 — Data Management

This page has one tab per dataset. It describes the selected dataset and shows whether saved models/metrics are available, along with data summary and model information. The page reads precomputed JSON and model files; opening the page does not train models.

**Demo tip:** select each tab and state its task, target label, available/used rows, and whether it is synthetic or a benchmark. Make clear that the page reports local files and saved artifacts.

### Page 2 — Model Evaluation

This page lets a viewer inspect saved model results for each dataset. Depending on available metrics, it presents model comparison tables, best-model callouts, threshold and metric information, and evaluation charts.

**Demo tip:** use one dataset to explain a confusion matrix or threshold. Point out that the F1-best model is chosen from supervised models; AUC-best and F1-best need not be the same model. Do not call high ROC-AUC “98% accurate”: AUC and accuracy measure different things.

### Page 3 — Digital Twin Simulator

The simulator lets a user select a domain and a number of forecast steps, then plots sample trajectories and an intervention comparison. `modules/digital_twin.py` stores transition probabilities among Normal, Risk, and Fraud states for each domain. Each run samples transitions stochastically. It assigns score ranges by state and, in the intervention case, multiplies the score by 0.35 after a Fraud state persists beyond the initial steps.

The page itself states that this is a rule-based scenario simulator. The transition values and intervention are configured in code; the simulation is not fitted to the benchmark data. Although internal names include “DRL,” the current code does not train a reinforcement-learning agent or learn a policy. Present it as an illustrative what-if component.

### Page 4 — Live Prediction

The viewer chooses a dataset and a saved model, enters the fields shown in that dataset's form, and selects **Analyze Transaction**. The app invokes the saved preprocessing/model pipeline, displays a score, compares it with the selected threshold, and renders an alert/risk label. It may also show model-score comparisons and a simplified explanation.

Example forms have prefilled values for demonstration. Treat them as crafted examples, not proof of generalization. The form uses a limited set of inputs; where a saved model was trained on more fields, the prediction code fills missing features using its stored medians or neutral values. A real operational interface would need a documented, complete feature contract and validation of its input values.

### Page 5 — Executive Insights

This page summarizes dataset sizes, positive-class ratios, best model names, F1 and AUC, class-distribution plots, feature-importance charts when supported, and guidance for interpreting metrics. It is designed to give a concise overview after the detailed evaluation page.

**Current content issue to be aware of:** the Executive Insights code contains a note saying BankSim and IEEE-CIS files are synthetic. That message conflicts with the dataset source/training setup documented in `data/DATA_SOURCES.md` and `download_datasets.py`, which prepare the published BankSim simulator dataset and the labeled IEEE-CIS/OpenML mirror. Verify which local files were used before presenting; the current saved statistics show 594,643 BankSim rows and 590,540 IEEE-CIS rows. The message should be corrected in the app so the UI and project documentation agree.

## 7. Metrics, thresholds, and current saved results

### What each metric answers

| Metric | Question answered | Caution |
|---|---|---|
| Accuracy | What fraction of all records were classified correctly? | Can appear high when the positive class is rare. |
| Precision | Of the alerts, what fraction were positive cases? | Low precision means many false alarms. |
| Recall | Of all positive cases, what fraction were detected? | Low recall means many missed positives. |
| F1-score | What is the harmonic balance of precision and recall? | Does not include the operational cost of a false alarm or a missed case. |
| PR-AUC | How does precision/recall trade off across score cutoffs? | Especially informative under imbalance, but still does not choose the deployment cutoff. |
| ROC-AUC | How well are positives ranked ahead of negatives across cutoffs? | Does not by itself establish a useful precision at a chosen operating point. |
| Balanced accuracy | What is the average of class-specific recall values? | Does not directly show alert volume or false-alarm cost. |

At a particular threshold, a model labels a record positive when its score is at or above that cutoff. Lowering a threshold usually increases recall and can also increase false positives; raising it usually reduces alerts and can miss more positives. Threshold choice should be driven by the use case, review capacity, and the relative cost of missed cases and false alarms.

### Saved results at the time this guide was written

The following are the values in the current `models/evaluation_metrics.json`. “Best by F1” is the saved best supervised model for each dataset. These are holdout benchmark results for this project configuration and should be refreshed after retraining.

| Dataset | Best by F1 | Accuracy | Precision | Recall | F1-score | ROC-AUC | Threshold |
|---|---|---:|---:|---:|---:|---:|---:|
| PaySim | XGBoost | 0.9995 | 0.7326 | 0.9844 | 0.8400 | 0.9935 | 0.005 |
| BankSim | Random Forest | 0.9534 | 0.1807 | 0.9386 | 0.3031 | 0.9920 | 0.500 |
| CICIDS2017 | XGBoost | 0.8781 | 0.6179 | 0.9992 | 0.7636 | 0.9989 | 0.005 |
| IEEE-CIS | Random Forest | 0.8771 | 0.1734 | 0.6828 | 0.2766 | 0.8684 | 0.500 |

These results illustrate why accuracy alone does not tell the full story. For BankSim, the saved Random Forest result has 95.34% accuracy, 18.07% precision, and 93.86% recall at a 0.5 cutoff. It identifies most positive cases but produces many false alarms. The low precision is an important project result and should not be hidden in a presentation.

### Important validation interpretation

- Metrics summarize the configured holdout, not unseen future periods or a live deployment.
- The best F1 is threshold-dependent; changing the threshold changes precision, recall, F1, accuracy, and confusion counts.
- High ROC-AUC does not guarantee high precision at the threshold used by the dashboard.
- Since multiple model/threshold combinations are evaluated on the same holdout, a selected best result can be optimistic as a final estimate. A separate validation set or nested evaluation would give a stronger estimate.
- For time-ordered datasets, the split may include tied timestamps at the boundary; as a result, the test share can differ from exactly 20%.
- Performance across different datasets is not directly comparable because task, feature set, positive rate, source, and sampling differ.

## 8. Reproducing the current workflow

### Environment

Python 3.10–3.12 is recommended. The model stack includes Streamlit, pandas, NumPy, scikit-learn, imbalanced-learn, XGBoost, joblib, and plotting/explanation packages. IEEE conversion uses `pyarrow`. See `requirements.txt` and [`INSTALLATION.md`](INSTALLATION.md) for current dependencies and setup guidance.

### Windows PowerShell setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Download and prepare data

```powershell
python .\download_datasets.py
```

The downloader prepares all four local sources and inspection previews. It checks downloaded compressed/archived inputs and verifies selected IEEE-CIS row/label counts before writing. Network access is needed for any source not already present. Source access rules and attribution remain applicable.

### Train models

Train every configured dataset:

```powershell
python .\offline_trainer.py
```

Train only BankSim and IEEE-CIS:

```powershell
python .\offline_trainer.py --datasets banksim,ieee
```

This writes model pipelines and updates `models/evaluation_metrics.json` and `models/dataset_stats.json`. Training all data may take several minutes or longer and can require substantial memory, especially for the large data files and model artifacts.

### Re-evaluate saved models without retraining

```powershell
python .\offline_trainer.py --evaluate-existing
```

To target specific datasets:

```powershell
python .\offline_trainer.py --evaluate-existing --datasets banksim,ieee
```

This reloads each selected dataset, evaluates existing model files on the recreated holdout, and refreshes metrics and statistics. Use the same data, configuration, software versions, and random seed when trying to reproduce a saved result.

### Launch dashboard

```powershell
streamlit run app.py
```

Open the localhost URL printed in the terminal, usually `http://localhost:8501`. The dashboard reads pre-trained files from `models/`; it does not train upon launch. If results do not appear, check that the corresponding dataset files, model `.pkl` files, JSON metrics, and statistics exist.

## 9. Suggested end-to-end demo

1. Start from **Data Management** and show that all four datasets have saved models.
2. Explain the task and label for each dataset, including that CICIDS is network intrusion and PaySim/BankSim are simulated data.
3. Move to **Model Evaluation** and select one dataset. Explain its positive class, row count, and threshold.
4. Read precision and recall together. Use BankSim to discuss high recall versus false alarms, or PaySim to discuss the low threshold and rare positive class.
5. Open **Live Prediction**, show the selected model and threshold, enter or retain a crafted example, and run the score. Say it is a demonstration input scored locally.
6. Open **Digital Twin Simulator**, choose a domain and number of steps, generate a scenario, and explain the configured transition and rule-based intervention.
7. Finish in **Executive Insights** with the F1 comparison and next steps.

### Suggested 90-second spoken explanation

“Nexus Fraud Defense is an interactive prototype for studying fraud and intrusion detection. It prepares PaySim, BankSim, IEEE-CIS, and CICIDS2017 data, selects the configured features, removes the target from model inputs, and evaluates four approaches: Logistic Regression, Random Forest, XGBoost, and Isolation Forest. The application separates training and holdout data and reports accuracy, precision, recall, F1, AUC, and the decision threshold. This matters because fraud is rare and a high accuracy value can hide missed cases or false alarms. The dashboard also lets me score an example locally and explore configured risk scenarios. These are benchmark demonstrations: the simulator is rule-based and the prediction page does not connect to live payment systems. The next step is external validation and threshold selection for a clearly defined operating cost.”

## 10. Presentation outline

| Slide | Suggested content |
|---:|---|
| 1 | Project title, author/supervisor details, and one-sentence purpose. |
| 2 | Problem statement: rare positive cases and the cost of false alarms/missed cases. |
| 3 | Objectives and scope, including prototype boundaries. |
| 4 | Dataset table: domains, labels, row counts, class imbalance, and provenance. |
| 5 | Method diagram: load → select/clean → split → pipeline/model → evaluate → dashboard. |
| 6 | Model approaches and why a supervised baseline, tree models, and anomaly detection are compared. |
| 7 | Metrics and saved results; emphasize precision/recall and thresholds. |
| 8 | Dashboard demo screenshots: evaluation, example scoring, and scenario simulator. |
| 9 | Limitations, validation needed, and responsible-use considerations. |
| 10 | Conclusion and future work. |

## 11. Common panel questions and suggested answers

**Why did you use multiple datasets?**  
To demonstrate the same general preparation, evaluation, and dashboard workflow across different domains. The resulting scores are not a direct competition because the datasets and prediction tasks differ.

**Why does the project include CICIDS2017 in a fraud framework?**  
It demonstrates the broader anomaly/fraud-detection workflow on network intrusion data. In the dashboard it is a distinct cybersecurity classification task, not financial fraud.

**Why can accuracy be misleading?**  
When fraud is rare, predicting mostly normal examples can yield high accuracy. Recall, precision, F1, and confusion counts show whether positive cases are found and how many false alerts result.

**What is the difference between precision and recall?**  
Precision describes how trustworthy the alerts are. Recall describes how many of the actual positive cases the system catches.

**Why is a threshold needed?**  
The model outputs a score, and the threshold turns it into a yes/no decision. A different cutoff changes the alert and miss trade-off.

**Why compare Isolation Forest with classifiers?**  
It demonstrates an unsupervised anomaly-detection approach alongside supervised methods. It should be interpreted separately because its training and score semantics differ.

**Is the digital twin learned from transaction data?**  
No. It uses configured transition matrices and a hand-coded intervention effect to create illustrative trajectories. It is not a trained digital replica or reinforcement-learning agent.

**What does live prediction mean here?**  
It means an interactive form scores a manually entered example through a locally saved pipeline. It does not mean live transaction stream processing.

**Can you guarantee these metrics on real-world transactions?**  
No. These are saved holdout benchmark results. New populations, time periods, data-quality issues, and operational conditions can change performance. Independent validation is required.

**What would you improve next?**  
Resolve the stale dataset description in the Executive Insights UI; validate on a separate later-period dataset; define false-positive and false-negative costs before threshold selection; test complete prediction inputs; evaluate calibration and drift; and test the dashboard on a clean environment.

## 12. Known caveats and next development steps

This section records issues a presenter or future developer should know about. It distinguishes current implementation from planned improvement.

### Current caveats

1. **Executive Insights text needs a correction.** The page currently labels BankSim and IEEE-CIS files synthetic, while the downloader and source notes describe published BankSim simulator and IEEE-CIS labeled benchmark sources. Correct the sentence to distinguish BankSim's synthetic nature from IEEE-CIS benchmark records.
2. **The simulator is illustrative.** It is stochastic and uses configured transition probabilities. Repeated runs may produce different paths. The intervention modifies generated scores; it does not prove a real mitigation would reduce fraud.
3. **The project uses different problem domains.** A binary output has different meaning for network attacks and financial transactions. Avoid presenting the combined dashboard as one universal classifier.
4. **Sample size is a deliberate runtime trade-off.** The saved PaySim and CICIDS results use capped samples, not every available record. BankSim and IEEE-CIS use all rows reported in the current saved stats.
5. **Manual scoring may have missing fields.** The prediction form uses a small set of human-entered features. Other saved-model inputs are filled or aligned by the pipeline, which is a demo convenience and should be validated before operational use.
6. **Model score calibration is not established.** A numeric score is not automatically a calibrated probability. This is particularly important for Isolation Forest's anomaly output.
7. **Dashboard wording should stay careful.** Labels such as “blocking” or “attack detected” can sound like automatic operational action even though no external system is connected. Describe them as model classifications/alerts in this prototype.

### Recommended future work

- Correct the stale BankSim/IEEE statement in the Executive Insights page.
- Add a clean-start walkthrough that verifies data, model artifacts, dependency installation, and all five pages.
- Create an independent validation set or repeated time-based evaluation that is not used to select the reported model/threshold.
- Report confusion matrices and alert counts alongside headline metrics for each dataset.
- Define a real use case's review capacity and error costs before choosing an operating threshold.
- Validate model calibration and test for drift across time and populations.
- Make the example scoring form collect all required fields, or clearly show which model inputs are imputed.
- Add repeatable test records and checks for missing data, invalid values, and serialized model compatibility.
- Keep the digital twin described as a simulation until transitions are learned/validated against a suitable system and the intervention is evaluated rigorously.
- Record package versions, data hashes, training configuration, and model version with each result for reproducibility.

## 13. Useful links in this repository

- [Short README and quick overview](README.md)
- [Installation guide](INSTALLATION.md)
- [Data sources and provenance](data/DATA_SOURCES.md)
- [Development notes](DEVELOPMENT.md)
- [PowerPoint generation notes](README_generate_ppt.md)


