import numpy as np
import pandas as pd
import joblib
import json
import time
import os
import warnings
warnings.filterwarnings("ignore")

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score,
    recall_score, classification_report, confusion_matrix
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from sleem_model import SLEEM, Individual
from generate_dataset import SYMPTOM_COLS

SEED = 42
np.random.seed(SEED)
FEATURES = SYMPTOM_COLS


def load_csv(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    target = next((c for c in ["prognosis", "condition"] if c in df.columns), None)
    if not target:
        raise ValueError(f"No target column in {path}")
    y = df[target].dropna()
    y = y[y.str.strip() != ""]
    X = pd.DataFrame({f: df[f].fillna(0).astype(int) if f in df.columns else 0
                      for f in FEATURES})
    return X.loc[y.index].values, y.values


def score(y_true, y_pred):
    return {
        "accuracy":        round(accuracy_score(y_true, y_pred) * 100, 2),
        "macro_f1":        round(f1_score(y_true, y_pred, average="macro", zero_division=0), 4),
        "macro_precision": round(precision_score(y_true, y_pred, average="macro", zero_division=0), 4),
        "macro_recall":    round(recall_score(y_true, y_pred, average="macro", zero_division=0), 4),
    }


def main():
    os.makedirs("paper_results", exist_ok=True)

    print("=" * 56)
    print("  SLEEM — Paper Evaluation")
    print("=" * 56)

    # ── Load data ──────────────────────────────────────────────
    print("\n[1/5] Loading dataset...")
    data_path = next(
        (p for p in [
            "datasets/final_training_data.csv",
            "datasets/synthetic_training_data.csv"
        ] if os.path.exists(p)),
        None
    )
    if not data_path:
        print("ERROR: No dataset found. Run train_model.py first.")
        return

    X, y_raw = load_csv(data_path)
    le = LabelEncoder()
    y  = le.fit_transform(y_raw)
    n_classes = len(le.classes_)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )
    print(f"  Train: {len(X_train)} | Test: {len(X_test)} | Classes: {n_classes}")

    # ── Load SLEEM ─────────────────────────────────────────────
    print("\n[2/5] Loading SLEEM...")
    if not os.path.exists("models/sleem_model.pkl"):
        print("ERROR: models/sleem_model.pkl not found. Run train_model.py first.")
        return
    sleem = joblib.load("models/sleem_model.pkl")
    with open("models/model_meta.json") as f:
        meta = json.load(f)

    # ── Train baselines ────────────────────────────────────────
    print("\n[3/5] Training baselines...")
    baselines = {
        "Random Forest": RandomForestClassifier(
            n_estimators=300, max_depth=12,
            class_weight="balanced", random_state=SEED
        ),
        "XGBoost": XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            objective="multi:softprob", num_class=n_classes,
            eval_metric="mlogloss", use_label_encoder=False,
            verbosity=0, random_state=SEED
        ),
        "Extra Trees": ExtraTreesClassifier(
            n_estimators=300, max_depth=12,
            class_weight="balanced", random_state=SEED
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            class_weight="balanced", random_state=SEED, verbosity=-1
        ),
    }

    results  = []
    trained  = {}

    for name, model in baselines.items():
        print(f"  {name}...", end=" ", flush=True)
        t0 = time.time()
        model.fit(X_train, y_train)
        train_sec = round(time.time() - t0, 2)
        t1 = time.time()
        preds = model.predict(X_test)
        infer_ms = round((time.time() - t1) * 1000 / len(X_test), 4)
        s = score(y_test, preds)
        print(f"Acc={s['accuracy']}%  F1={s['macro_f1']}")
        results.append({"model": name, **s,
                        "train_time_sec": train_sec,
                        "infer_ms_per_sample": infer_ms})
        trained[name] = model

    # Static RF+XGB ensemble
    print("  RF+XGB Static Ensemble...", end=" ", flush=True)
    rf_p  = trained["Random Forest"].predict_proba(X_test)
    xgb_p = trained["XGBoost"].predict_proba(X_test)
    ens_preds = ((rf_p + xgb_p) / 2).argmax(axis=1)
    s = score(y_test, ens_preds)
    print(f"Acc={s['accuracy']}%  F1={s['macro_f1']}")
    results.append({"model": "RF+XGB Static Ensemble", **s,
                    "train_time_sec": "N/A", "infer_ms_per_sample": "N/A"})

    # ── Evaluate SLEEM ─────────────────────────────────────────
    print("\n[4/5] Evaluating SLEEM...")
    t1 = time.time()
    sleem_probs = sleem.predict_proba(X_test)
    sleem_preds = np.argmax(sleem_probs, axis=1)
    infer_ms    = round((time.time() - t1) * 1000 / len(X_test), 4)
    s = score(y_test, sleem_preds)
    print(f"  Acc={s['accuracy']}%  F1={s['macro_f1']}  "
          f"Prec={s['macro_precision']}  Rec={s['macro_recall']}")
    results.append({"model": "SLEEM (proposed)", **s,
                    "train_time_sec": "see model_meta.json",
                    "infer_ms_per_sample": infer_ms})

    # ── Save outputs ───────────────────────────────────────────
    print("\n[5/5] Saving results...")

    with open("paper_results/baseline_comparison.json", "w") as f:
        json.dump(results, f, indent=2)

    report = classification_report(
        y_test, sleem_preds,
        target_names=le.classes_, output_dict=True, zero_division=0
    )
    per_class = [
        {"condition": cls,
         "precision": round(report[cls]["precision"], 4),
         "recall":    round(report[cls]["recall"],    4),
         "f1":        round(report[cls]["f1-score"],  4),
         "support":   int(report[cls]["support"])}
        for cls in le.classes_
    ]
    with open("paper_results/per_class_report.json", "w") as f:
        json.dump(per_class, f, indent=2)

    cm = confusion_matrix(y_test, sleem_preds)
    np.fill_diagonal(cm, 0)
    flat    = cm.flatten()
    top_idx = flat.argsort()[-10:][::-1]
    confused = [
        {"true_condition":      le.classes_[r],
         "predicted_condition": le.classes_[c],
         "count":               int(cm[r, c])}
        for idx in top_idx
        for r, c in [divmod(idx, n_classes)]
        if cm[r, c] > 0
    ]
    with open("paper_results/confused_pairs.json", "w") as f:
        json.dump(confused, f, indent=2)

    with open("paper_results/evolution_history.json", "w") as f:
        json.dump(meta.get("evolution_history", []), f, indent=2)

    best_info = {
        "model_types": meta["best_model_types"],
        "weights":     meta["best_model_weights"],
        "n_models":    len(meta["best_model_types"])
    }
    with open("paper_results/best_individual.json", "w") as f:
        json.dump(best_info, f, indent=2)

    # ── Print summary ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    print(f"  {'Model':<32} {'Acc%':>7} {'F1':>7} {'Prec':>7} {'Rec':>7}")
    print("  " + "-" * 56)
    for r in results:
        print(f"  {r['model']:<32} "
              f"{str(r['accuracy']):>7} "
              f"{str(r['macro_f1']):>7} "
              f"{str(r['macro_precision']):>7} "
              f"{str(r['macro_recall']):>7}")
    print("=" * 60)

    print("\n  Top confused pairs (SLEEM):")
    for p in confused[:5]:
        print(f"    {p['true_condition']:<35} -> "
              f"{p['predicted_condition']:<35} ({p['count']} times)")

    print(f"\n  Best evolved individual:")
    print(f"    Models:  {best_info['model_types']}")
    print(f"    Weights: {best_info['weights']}")

    print("\n  Evolution history:")
    for g in meta.get("evolution_history", []):
        bar = "█" * int(g["best_accuracy"] * 30)
        print(f"    Gen {g['generation']:>2}: {g['best_accuracy']:.4f}  {bar}")

    print("\n  Files saved to paper_results/")
    print("  Send these 5 files for paper writing:")
    for f in ["baseline_comparison.json","per_class_report.json",
              "confused_pairs.json","evolution_history.json","best_individual.json"]:
        print(f"    paper_results/{f}")


if __name__ == "__main__":
    main()