"""
Model Training and Evaluation  -  Anti-Overfitting Pipeline

Key design decisions:
  1. SMOTE on training data only
  2. Train/test split happens before any fitting
  3. A single pipeline handles training and inference
  4. Fraud threshold = 0.25 (not 0.5)
"""

import os, time
import numpy as np
import pandas as pd
import joblib
import streamlit as st
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import (
    accuracy_score, balanced_accuracy_score, average_precision_score,
    precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix,
)
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.combine import SMOTETomek
import xgboost as xgb

from config import MODEL_CONFIG, MODELS_DIR, DATA_CONFIG, FRAUD_THRESHOLD, TUNING_CONFIG


def _ensure_dir():
    os.makedirs(MODELS_DIR, exist_ok=True)

def _neg_pos_ratio(y):
    return max(1.0, int((y == 0).sum()) / max(1, int((y == 1).sum())))

def _build_preprocessor(X):
    # Select categorical targets mimicking exact user fields explicitly preventing 'isnan' exceptions natively 
    cat_cols = ["type", "category", "gender", "age", "ProductCD", "card4", "card6", "P_emaildomain", "DeviceType"] + [f"M{i}" for i in range(1, 10)]
    cat_cols = [c for c in cat_cols if c in X.columns]
    num_cols = [c for c in X.columns if c not in cat_cols]
    
    numeric_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, num_cols),
            ('cat', categorical_transformer, cat_cols)
        ],
        remainder='passthrough'
    )
    return preprocessor

def build_model_pipeline(model_name, classifier, X, y, ds_key=None):
    from modules.data_loader import DomainFeatureExtractor
    
    # 🔴 1. STRICT ANTI-LEAKAGE ASSERTION (ROOT CAUSE FIX)
    leak_cols = ["fraud", "isFraud", "is_fraud", "Class", "Label", "label"]
    for col in leak_cols:
        if col in X.columns:
            raise AssertionError(f"STRICT LEAKAGE DETECTED: Column '{col}' must be dropped before training.")

    extractor = DomainFeatureExtractor(raw_features=list(X.columns))
    preprocessor = _build_preprocessor(X) # Note: _build_preprocessor was used on raw X in previous logic, let's keep it consistent
    
    steps = [('extractor', extractor), ('preprocessor', preprocessor)]
    
    # 🟢 2. APPLY SMOTETomek ONLY FOR IMBALANCED DATASETS (PaySim, BankSim, IEEE-CIS)
    is_imbalanced = ds_key not in ("cicids", "cicids2017", "banksim", "ieee")
    
    # Keep the published BankSim/IEEE class distributions intact. For those datasets,
    # classifiers use class weights instead of creating synthetic minority examples.
    if is_imbalanced and model_name != "Isolation Forest":
        # k_neighbors logic from SMOTE can be passed to the underlying SMOTE in SMOTETomek if needed
        # but standard SMOTETomek(random_state=42) is preferred as per request
        smote_tomek = SMOTETomek(random_state=42)
        steps.append(('smote_tomek', smote_tomek))
        
    steps.append(('classifier', classifier))
    return ImbPipeline(steps)


# ---- Individual trainers ----

def _train_lr(X, y, ds_key=None):
    params = MODEL_CONFIG["logistic_regression"].copy()
    if ds_key in ("banksim", "ieee"):
        params["class_weight"] = "balanced"
    base_m = LogisticRegression(**params)
    pipe = build_model_pipeline("Logistic Regression", base_m, X, y, ds_key=ds_key)
    
    pipe.fit(X, np.asarray(y))
    return pipe

def _train_rf(X, y, ds_key=None):
    params = MODEL_CONFIG["random_forest"].copy()
    if ds_key and ds_key in TUNING_CONFIG:
        params.update(TUNING_CONFIG[ds_key].get("rf", {}))
        
    if ds_key in ("banksim", "ieee"):
        params["class_weight"] = "balanced_subsample"
    base_m = RandomForestClassifier(**params)
    pipe = build_model_pipeline("Random Forest", base_m, X, y, ds_key=ds_key)
    
    pipe.fit(X, np.asarray(y))
    return pipe

def _train_xgb(X, y, ds_key=None):
    p = MODEL_CONFIG["xgboost"].copy()
    if ds_key in ("banksim", "ieee"):
        p["scale_pos_weight"] = max(1.0, float((y == 0).sum()) / max(1, int((y == 1).sum())))
    if ds_key in TUNING_CONFIG:
        p.update(TUNING_CONFIG[ds_key].get("xgb", {}))
    base_m = xgb.XGBClassifier(**p)
    pipe = build_model_pipeline("XGBoost", base_m, X, y, ds_key=ds_key)
    
    pipe.fit(X, np.asarray(y))
    return pipe

def _train_if(X, y, ds_key=None):
    p = MODEL_CONFIG["isolation_forest"].copy()
    p["contamination"] = max(0.001, min(float((y == 1).mean()), 0.5))
    m = IsolationForest(**p)
    pipe = build_model_pipeline("Isolation Forest", m, X, y, ds_key=ds_key)
    # Isolation forest fits unsupervised on Xs
    pipe.fit(X)
    return pipe

TRAINERS = {
    "Logistic Regression": _train_lr,
    "Random Forest": _train_rf,
    "XGBoost": _train_xgb,
    "Isolation Forest": _train_if,
}


# ---- Probabilities and predictions ----

def get_probabilities(model, X, name):
    try:
        # 1. FIX ML PROBABILITY = 0 ISSUE
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(X)
            # Ensure it's 2D and has at least two classes (for binary)
            if probs.ndim == 2 and probs.shape[1] > 1:
                return probs[:, 1]
            else:
                return probs.flatten()
        elif hasattr(model, "decision_function"):
            raw = model.decision_function(X)
            # IsolationForest assigns lower decision scores to anomalies.
            if name == "Isolation Forest":
                raw = -raw
            return 1.0 / (1.0 + np.exp(-np.clip(raw, -50, 50)))
    except Exception as e:
        print(f"Prediction Probability Bounds Error ({name}): {e}")
        pass
    
    # Fallback to binary if proba fails
    try:
        predictions = model.predict(X)
        return np.array([1.0 if p == 1 else 0.0 for p in predictions])
    except:
        return np.zeros(len(X))

def get_predictions(model, X, name, threshold=None):
    t = threshold or FRAUD_THRESHOLD
    # Isolation Forest specific handling moved out of primary prediction loop if possible
    # but kept here for internal evaluation consistency
    if name == "Isolation Forest":
        return (model.predict(X) == -1).astype(int)
    return (get_probabilities(model, X, name) >= t).astype(int)

# ---- Removed Cross-Validation ----

# ---- Evaluation ----

def evaluate_model(model, X, y, name, threshold=None, ds_key=None):

    probs = get_probabilities(model, X, name)

    # Do NOT tune threshold on the test set (prevents optimistic bias).
    # Use provided threshold, dataset-specific tuning config, or global FRAUD_THRESHOLD.
    if threshold is not None:
        best_thresh = threshold
    elif ds_key is not None:
        best_thresh = _load_selected_threshold(ds_key, name)
    else:
        best_thresh = FRAUD_THRESHOLD

    preds = get_predictions(model, X, name, threshold=best_thresh)

    metrics = {
        "Accuracy": round(accuracy_score(y, preds), 4),
        "Balanced_Accuracy": round(balanced_accuracy_score(y, preds), 4),
        "PR-AUC": round(average_precision_score(y, probs), 4),
        "Precision": round(precision_score(y, preds, zero_division=0), 4),
        "Recall": round(recall_score(y, preds, zero_division=0), 4),
        "F1-Score": round(f1_score(y, preds, zero_division=0), 4),
        "Best_Threshold": round(float(best_thresh), 3)
    }
    
    cm = confusion_matrix(y, preds)
    if cm.shape == (2, 2):
        tn, fp, fn_val, tp = cm.ravel()
    else:
        tn = fp = fn_val = tp = 0
    metrics["CM"] = {"TN": int(tn), "FP": int(fp), "FN": int(fn_val), "TP": int(tp)}
    try:
        from sklearn.metrics import roc_curve, roc_auc_score
        auc_score = roc_auc_score(y, probs)
        metrics["ROC-AUC"] = round(auc_score, 4)
        fpr, tpr, _ = roc_curve(y, probs)
        
        # Downsample ROC to roughly ~100 points
        if len(fpr) > 100:
            indices = np.linspace(0, len(fpr) - 1, 100).astype(int)
            fpr = fpr[indices]
            tpr = tpr[indices]
        
        metrics["ROC_CURVE"] = {"fpr": fpr.tolist(), "tpr": tpr.tolist()}
    except Exception:
        metrics["ROC-AUC"] = 0.0

    return metrics, preds, probs


# ---- Full training pipeline ----

def train_and_evaluate_all(X_train, y_train, X_test, y_test,
                           model_names=None, use_smote=True, progress_cb=None, ds_key=None):
    if model_names is None:
        from config import MODEL_NAMES
        model_names = MODEL_NAMES

    results, models, timings = {}, {}, {}

    for i, name in enumerate(model_names):
        if progress_cb:
            progress_cb(i, len(model_names), f"Training {name}...")
        t0 = time.time()
        try:
            trainer = TRAINERS.get(name)
            if not trainer:
                continue
            model = trainer(X_train, y_train, ds_key=ds_key)
            timings[name] = round(time.time() - t0, 2)

            met, _, _ = evaluate_model(model, X_test, y_test, name, ds_key=ds_key)
            results[name] = met
            models[name] = model

        except Exception as e:
            # Enhanced CLI logging for background training
            msg = f"Error training {name}: {str(e)}"
            print(f"  [ERROR] {msg}")
            if 'st' in globals():
                try: st.warning(msg)
                except: pass
            timings[name] = 0

    if progress_cb:
        progress_cb(len(model_names), len(model_names), "Done")

    # Select best model based on F1-Score (Primary) and Recall (Secondary)
    # 9. REMOVE Isolation Forest as primary model (comparison only)
    candidate_results = {k: v for k, v in results.items() if k != "Isolation Forest"}
    
    if not candidate_results:
        candidate_results = results

    best = max(candidate_results, key=lambda k: (candidate_results[k].get("F1-Score", 0), candidate_results[k].get("Recall", 0))) if candidate_results else None
    return results, models, best, timings


# ---- Hybrid prediction (ML + rules) ----

def _load_selected_threshold(ds_key, model_name):
    import json
    # precedence: models/thresholds_selected.json -> TUNING_CONFIG -> models/evaluation_metrics.json -> FRAUD_THRESHOLD
    try:
        with open("models/thresholds_selected.json", "r") as f:
            tsel = json.load(f)
            if ds_key in tsel:
                # keys in thresholds file may be model display names
                value = tsel[ds_key].get(model_name, tsel[ds_key].get(model_name.lower()))
                if isinstance(value, dict):
                    value = value.get("threshold")
                if value is not None:
                    return float(value)
    except Exception:
        pass
    try:
        if ds_key in TUNING_CONFIG and TUNING_CONFIG[ds_key].get("threshold") is not None:
            return float(TUNING_CONFIG[ds_key].get("threshold"))
    except Exception:
        pass
    try:
        with open("models/evaluation_metrics.json", "r") as f:
            em = json.load(f)
            m = em.get(ds_key, {}).get("results", {}).get(model_name, {})
            if m and m.get("Best_Threshold") is not None:
                return float(m.get("Best_Threshold"))
    except Exception:
        pass
    return FRAUD_THRESHOLD


def predict_fraud(model, X_input, model_name, raw_tx=None, ds_key=None):
    """Hybrid prediction: ML pipeline + risk assessment.
    Uses dataset-specific calibrated threshold when available (ds_key).
    """
    # Align input to match pipeline's expected raw features
    expected_features = None
    if hasattr(model, "named_steps") and "extractor" in model.named_steps:
        expected_features = list(model.named_steps["extractor"].raw_features or [])

    if expected_features:
        missing = [c for c in expected_features if c not in X_input.columns]
        extra = [c for c in X_input.columns if c not in expected_features]
        if missing:
            # The live form asks for core fields only. For additional model features,
            # use training-set medians/missing-category sentinels as neutral values.
            extractor = model.named_steps["extractor"]
            medians = getattr(extractor, "medians_", {})
            for mc in missing:
                X_input[mc] = medians.get(mc, "__MISSING__" if mc.startswith("M") else 0)
        if extra:
            X_input = X_input[expected_features].copy()

    # Let the pipeline handle feature transformation/preprocessing.
    # Avoid reindexing to classifier feature names which can zero-out raw inputs.
    probs = get_probabilities(model, X_input, model_name)
    ml_prob = float(probs[0])

    # determine threshold
    threshold = FRAUD_THRESHOLD if ds_key is None else _load_selected_threshold(ds_key, model_name)
    pred = int(ml_prob >= threshold)

    if ml_prob > 0.6:
        level = "CRITICAL / HIGH RISK"
    elif ml_prob >= threshold:
        level = "ELEVATED RISK"
    else:
        level = "LEGITIMATE / LOW RISK"

    return pred, ml_prob, {
        "ml_probability": ml_prob,
        "combined": ml_prob,
        "risk_level": level,
        "factors": [],
        "threshold": float(threshold),
    }


# ---- Feature importance ----

def get_feature_importance(model, feat_names, model_name):
    """Return feature importances from a fitted estimator or saved pipeline."""
    estimator = model
    names = list(feat_names or [])
    steps = getattr(model, "named_steps", {})
    if steps:
        estimator = steps.get("classifier", model)
        preprocessor = steps.get("preprocessor")
        if preprocessor is not None:
            try:
                names = list(preprocessor.get_feature_names_out())
            except Exception:
                pass

    if hasattr(estimator, "feature_importances_"):
        values = np.asarray(estimator.feature_importances_).ravel()
    elif hasattr(estimator, "coef_"):
        values = np.abs(np.asarray(estimator.coef_)[0]).ravel()
    else:
        return {}
    if len(names) != len(values):
        names = [f"Feature {i + 1}" for i in range(len(values))]
    importance = {name: float(value) for name, value in zip(names, values)}
    total = sum(importance.values())
    if total > 0:
        importance = {name: value / total for name, value in importance.items()}
    return dict(sorted(importance.items(), key=lambda item: item[1], reverse=True))


# ---- Persistence ----

def save_trained_model(model, ds, name):
    _ensure_dir()
    p = os.path.join(MODELS_DIR, f"best_{ds}_{name.lower().replace(' ','_')}.pkl")
    joblib.dump(model, p)
    return p

def load_trained_model(ds, name):
    _ensure_dir()
    p = os.path.join(MODELS_DIR, f"best_{ds}_{name.lower().replace(' ','_')}.pkl")
    return joblib.load(p) if os.path.exists(p) else None

def load_all_models(ds):
    from config import MODEL_NAMES
    return {n: m for n in MODEL_NAMES if (m := load_trained_model(ds, n)) is not None}

def save_all_models(d, ds):
    return {n: save_trained_model(m, ds, n) for n, m in d.items()}

def calculate_confusion_matrix_metrics(y_true, y_pred):
    cm = confusion_matrix(y_true, y_pred)
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
    else:
        tn = fp = fn = tp = 0
    return {"TP": tp, "TN": tn, "FP": fp, "FN": fn}


def evaluate_models_cv(X, y, model_names=None, cv_folds=5, ds_key=None):
    """
    Perform stratified CV for each model trainer and return mean/std metrics.
    Returns a dict: {model_name: {"accuracy_mean":..., "accuracy_std":..., "all_scores":[...]}}
    """
    from sklearn.model_selection import StratifiedKFold

    if model_names is None:
        from config import MODEL_NAMES
        model_names = MODEL_NAMES

    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    results = {name: [] for name in model_names}

    X_np = X.copy()
    y_np = y.copy()

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_np, y_np)):
        X_train_fold = X_np.iloc[train_idx]
        y_train_fold = y_np.iloc[train_idx]
        X_val_fold = X_np.iloc[val_idx]
        y_val_fold = y_np.iloc[val_idx]

        for name in model_names:
            trainer = TRAINERS.get(name)
            if not trainer:
                continue
            try:
                model = trainer(X_train_fold, y_train_fold, ds_key=ds_key)
                met, preds, probs = evaluate_model(model, X_val_fold, y_val_fold, name, threshold=FRAUD_THRESHOLD, ds_key=ds_key)
                results[name].append(met.get("Accuracy", 0.0))
            except Exception as e:
                results[name].append(0.0)

    summary = {}
    for name, scores in results.items():
        arr = np.array(scores)
        summary[name] = {
            "accuracy_mean": float(np.nanmean(arr)) if len(arr) > 0 else 0.0,
            "accuracy_std": float(np.nanstd(arr)) if len(arr) > 0 else 0.0,
            "all_scores": [float(x) for x in arr.tolist()]
        }

    return summary


# ---- Helper functions for explainability ----

def _extract_estimator(model):
    """Extract the base estimator from a pipeline."""
    if hasattr(model, 'named_steps'):
        return model.named_steps.get('classifier', model)
    return model

def _predict_scores(model, X):
    """Get fraud probability scores from a model."""
    return get_probabilities(model, X, "model")
