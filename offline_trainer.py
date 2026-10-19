import os
import json
import joblib
import pandas as pd
import warnings
import argparse
from modules.data_loader import prepare_dataset
from modules.model_trainer import train_and_evaluate_all, save_all_models, load_all_models, evaluate_model, MODELS_DIR
from config import DATASET_META

warnings.filterwarnings("ignore")

def _validate_results(all_metrics):
    """
    Post-training validation:
      - No dataset shows constant 1.0 accuracy across ALL models
      - Best model's confusion matrix has FP > 0 and FN > 0
      - Metrics differ across datasets
    """
    print("\n--- VALIDATION ---")
    issues = []

    accuracies_by_ds = {}

    for ds_key, ds_data in all_metrics.items():
        results = ds_data.get("results", {})
        if not results:
            issues.append(f"  [WARN] {ds_key}: No model results found")
            continue

        # Check 1: Not all models should be 1.0 accuracy
        accs = [v.get("Accuracy", 0) for v in results.values()]
        if accs and all(a == 1.0 for a in accs):
            issues.append(f"  [FAIL] {ds_key}: ALL models show 1.0 accuracy — likely data leakage!")
        else:
            print(f"  [PASS] {ds_key}: Accuracy varies across models ({min(accs):.4f} - {max(accs):.4f})")

        accuracies_by_ds[ds_key] = accs

        # Check 2: Best model should have FP > 0 and FN > 0
        best = ds_data.get("best_model")
        if best and best in results:
            cm = results[best].get("CM", {})
            fp = cm.get("FP", 0)
            fn = cm.get("FN", 0)
            if fp == 0 and fn == 0:
                issues.append(f"  [WARN] {ds_key}/{best}: CM has FP=0 AND FN=0 — suspiciously perfect")
            else:
                print(f"  [PASS] {ds_key}/{best}: CM has FP={fp}, FN={fn} (realistic)")

    # Check 3: Metrics should differ across datasets
    if len(accuracies_by_ds) > 1:
        avg_accs = {k: sum(v)/len(v) for k, v in accuracies_by_ds.items() if v}
        vals = list(avg_accs.values())
        if len(set(round(v, 4) for v in vals)) == 1:
            issues.append("  [WARN] All datasets have identical average accuracy — suspicious")
        else:
            print(f"  [PASS] Metrics differ across datasets: {avg_accs}")

    if issues:
        print("\n  VALIDATION ISSUES:")
        for issue in issues:
            print(issue)
    else:
        print("\n  All validation checks passed!")

    return len(issues) == 0



def _write_json_atomic(path, value):
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as output:
        json.dump(value, output, indent=4)
    os.replace(temporary, path)


def refresh_saved_metrics(dataset_keys=None):
    """Recompute holdout metrics from saved models without retraining them."""
    dataset_keys = list(dataset_keys or DATASET_META.keys())
    unknown = sorted(set(dataset_keys) - set(DATASET_META))
    if unknown:
        raise ValueError(f"Unknown dataset key(s): {unknown}")
    metrics_path = os.path.join(MODELS_DIR, "evaluation_metrics.json")
    stats_path = os.path.join(MODELS_DIR, "dataset_stats.json")
    try:
        with open(metrics_path, "r", encoding="utf-8") as source:
            all_metrics = json.load(source)
    except (OSError, json.JSONDecodeError):
        all_metrics = {}
    try:
        with open(stats_path, "r", encoding="utf-8") as source:
            all_stats = json.load(source)
    except (OSError, json.JSONDecodeError):
        all_stats = {}

    for key in dataset_keys:
        print(f"[*] Evaluating saved {DATASET_META[key]['short_name']} models...")
        Xtr, Xte, ytr, yte, stats = prepare_dataset(key)
        models = load_all_models(key)
        if not models:
            print(f"  [SKIP] No saved models for {key}")
            continue
        results = {}
        for name, model in models.items():
            result, _, _ = evaluate_model(model, Xte, yte, name, ds_key=key)
            results[name] = result
            print(f"  {name}: F1={result['F1-Score']:.4f}, AUC={result.get('ROC-AUC', 0):.4f}, threshold={result['Best_Threshold']:.3f}")
        candidates = {name: row for name, row in results.items() if name != "Isolation Forest"} or results
        best = max(candidates, key=lambda name: (candidates[name].get("F1-Score", 0), candidates[name].get("Recall", 0)))
        previous = all_metrics.get(key, {})
        all_metrics[key] = {
            **previous,
            "best_model": best,
            "results": results,
            "feature_names": Xtr.columns.tolist(),
        }
        all_stats[key] = stats

    _write_json_atomic(metrics_path, all_metrics)
    _write_json_atomic(stats_path, all_stats)
    _validate_results(all_metrics)


def run_offline_training(dataset_keys=None):
    dataset_keys = list(dataset_keys or DATASET_META.keys())
    unknown = sorted(set(dataset_keys) - set(DATASET_META))
    if unknown:
        raise ValueError(f"Unknown dataset key(s): {unknown}")
    merge_existing = set(dataset_keys) != set(DATASET_META)
    print("================================================================")
    print(" INITIALIZING OFFLINE MODEL TRAINING")
    print("================================================================\n")
    
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)

    all_metrics = {}
    master_stats = {}
    if merge_existing:
        for path, target in ((os.path.join(MODELS_DIR, "evaluation_metrics.json"), all_metrics),
                             (os.path.join(MODELS_DIR, "dataset_stats.json"), master_stats)):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    target.update(json.load(f))
            except (OSError, json.JSONDecodeError):
                pass

    for ds_key in dataset_keys:
        meta = DATASET_META[ds_key]
        print(f"[*] Processing {meta['short_name']}...")
        print("  -> Loading and Preprocessing dataset...")
        
        try:
            Xtr, Xte, ytr, yte, stats = prepare_dataset(ds_key)
        except FileNotFoundError as e:
            print(f"  [SKIP] {meta['short_name']}: dataset file is missing ({e})")
            continue
        except Exception as e:
            print(f"  [CRITICAL ERROR] Failed to prepare {ds_key}: {e}")
            import traceback
            traceback.print_exc()
            raise e

        print(f"  -> Training features: {list(Xtr.columns)}")
        print(f"  -> Train shape: {Xtr.shape}, Fraud ratio: {ytr.mean():.4f}")
        print("  -> Training models...")
        results, models, best, timings = train_and_evaluate_all(Xtr, ytr, Xte, yte, ds_key=ds_key)
        
        # Save models
        save_all_models(models, ds_key)
        
        all_metrics[ds_key] = {
            "best_model": best,
            "results": results,
            "timings": timings,
            "feature_names": Xtr.columns.tolist(),
        }
        master_stats[ds_key] = stats
        
        # Print per-model results
        for mname, mresult in results.items():
            marker = " [BEST]" if mname == best else ""
            print(f"    {mname}: Acc={mresult.get('Accuracy',0):.4f} "
                  f"F1={mresult.get('F1-Score',0):.4f} "
                  f"AUC={mresult.get('ROC-AUC',0):.4f} "
                  f"Thresh={mresult.get('Best_Threshold',0):.3f}{marker}")
        print()

    # Save metrics
    metrics_path = os.path.join(MODELS_DIR, "evaluation_metrics.json")
    _write_json_atomic(metrics_path, all_metrics)

    stats_path = os.path.join(MODELS_DIR, "dataset_stats.json")
    _write_json_atomic(stats_path, master_stats)

    # Run validation
    _validate_results(all_metrics)

    print("\n================================================================")
    print(" TRAINING COMPLETE")
    print("================================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and save fraud-detection models.")
    parser.add_argument("--datasets", help="Comma-separated dataset keys (default: all configured datasets)")
    parser.add_argument("--evaluate-existing", action="store_true", help="Refresh metrics using saved models without retraining")
    args = parser.parse_args()
    selected = [key.strip() for key in args.datasets.split(",") if key.strip()] if args.datasets else None
    if args.evaluate_existing:
        refresh_saved_metrics(selected)
    else:
        run_offline_training(selected)
