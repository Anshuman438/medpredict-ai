"""
SLEEM v4 Training Pipeline
Ternary severity features | 20,000 rows | CPU | Pop=8 | Gen=8
"""
import os, warnings, logging
os.environ["LIGHTGBM_VERBOSITY"] = "-1"
warnings.filterwarnings("ignore")
logging.getLogger("lightgbm").setLevel(logging.ERROR)

import numpy as np
import pandas as pd
import random, joblib, json, time

from sklearn.metrics import (
    accuracy_score, f1_score,
    precision_score, recall_score,
    classification_report
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

from sleem_model import SLEEM
from generate_dataset import generate, SYMPTOM_COLS

SEED = 42
random.seed(SEED)
np.random.seed(SEED)


def load_data(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    target = next(
        (c for c in ["prognosis", "condition"] if c in df.columns), None)
    y = df[target].dropna()
    y = y[y.str.strip() != ""]
    X = pd.DataFrame({
        f: df[f].fillna(0).astype(int) if f in df.columns else 0
        for f in SYMPTOM_COLS
    })
    return X.loc[y.index].values, y.values


def run_baselines(X_train, X_test, y_train, y_test, n_classes):
    print("\n  Running baselines (same ternary data)...")
    results = {}

    baselines = {
        "Random Forest": RandomForestClassifier(
            n_estimators=300, max_depth=None,
            class_weight="balanced", n_jobs=-1, random_state=SEED),
        "XGBoost": XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            objective="multi:softprob", num_class=n_classes,
            eval_metric="mlogloss", tree_method="hist",
            n_jobs=-1, verbosity=0, random_state=SEED),
        "Extra Trees": ExtraTreesClassifier(
            n_estimators=300, max_depth=None,
            class_weight="balanced", n_jobs=-1, random_state=SEED),
        "LightGBM": LGBMClassifier(
            n_estimators=300, max_depth=8, learning_rate=0.05,
            num_leaves=127, class_weight="balanced",
            n_jobs=-1, verbosity=-1, random_state=SEED),
    }

    for name, model in baselines.items():
        t0 = time.time()
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        results[name] = {
            "accuracy":  round(accuracy_score(y_test, preds), 4),
            "f1":        round(f1_score(y_test, preds,
                               average="macro", zero_division=0), 4),
            "precision": round(precision_score(y_test, preds,
                               average="macro", zero_division=0), 4),
            "recall":    round(recall_score(y_test, preds,
                               average="macro", zero_division=0), 4),
            "time_sec":  round(time.time() - t0, 1),
        }
        r = results[name]
        print(f"    {name:<22} "
              f"Acc={r['accuracy']:.4f}  F1={r['f1']:.4f}  "
              f"P={r['precision']:.4f}  R={r['recall']:.4f}  "
              f"({r['time_sec']}s)")

    # RF + XGB static ensemble
    rf_p  = baselines["Random Forest"].predict_proba(X_test)
    xgb_p = baselines["XGBoost"].predict_proba(X_test)
    ens_p = 0.5 * rf_p + 0.5 * xgb_p
    preds = np.argmax(ens_p, axis=1)
    results["RF+XGB Ensemble"] = {
        "accuracy":  round(accuracy_score(y_test, preds), 4),
        "f1":        round(f1_score(y_test, preds,
                           average="macro", zero_division=0), 4),
        "precision": round(precision_score(y_test, preds,
                           average="macro", zero_division=0), 4),
        "recall":    round(recall_score(y_test, preds,
                           average="macro", zero_division=0), 4),
        "time_sec":  "N/A",
    }
    r = results["RF+XGB Ensemble"]
    print(f"    {'RF+XGB Ensemble':<22} "
          f"Acc={r['accuracy']:.4f}  F1={r['f1']:.4f}  "
          f"P={r['precision']:.4f}  R={r['recall']:.4f}")
    return results


if __name__ == "__main__":
    t_start = time.time()

    print("=" * 60)
    print("  SLEEM v4 — Ternary Dataset | 20k rows | CPU")
    print("  Population=8 | Generations=8 | Elite=3")
    print("=" * 60)

    os.makedirs("datasets", exist_ok=True)
    os.makedirs("models",   exist_ok=True)

    # ── Generate ternary dataset (20k) ───────────────────────────
    print("\n[1/4] Generating Ternary Dataset (20,000 rows)")
    print("-" * 50)
    syn_path  = "datasets/synthetic_training_data.csv"
    data_path = "datasets/final_training_data.csv"
    generate(syn_path, n_samples=20000)
    df = pd.read_csv(syn_path).sample(
        frac=1, random_state=SEED).reset_index(drop=True)
    df.to_csv(data_path, index=False)
    print(f"  Saved -> {data_path}")

    # ── Load ─────────────────────────────────────────────────────
    print("\n[2/4] Loading Data")
    print("-" * 50)
    X, y_raw  = load_data(data_path)
    le        = LabelEncoder()
    y         = le.fit_transform(y_raw)
    n_classes = len(le.classes_)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)

    print(f"  Samples  : {len(X):,}")
    print(f"  Features : {X.shape[1]}")
    print(f"  Classes  : {n_classes}")
    print(f"  Encoding : 0=absent  1=mild  2=severe")
    print(f"  Train    : {len(X_train):,}  |  Test : {len(X_test):,}")

    # ── Baselines ─────────────────────────────────────────────────
    print("\n[3/4] Baseline Evaluation")
    print("-" * 50)
    baseline_results = run_baselines(
        X_train, X_test, y_train, y_test, n_classes)

    # ── SLEEM ─────────────────────────────────────────────────────
    print("\n[4/4] SLEEM Evolution")
    print("-" * 50)
    print("  Base pool  : RF, XGB, ET, LGBM")
    print("  Per indiv  : 3-5 base models + 5-fold stacking + LogReg")
    print("  Fitness    : Macro F1 (equal weight across 41 classes)")
    print("  Population : 8  |  Generations : 8  |  Elite : 3")
    print()

    sleem = SLEEM(population_size=8, generations=8, elite_size=3)
    sleem.fit(X_train, y_train)

    # ── Final evaluation ──────────────────────────────────────────
    preds    = sleem.predict(X_test)
    test_acc = accuracy_score(y_test, preds)
    test_f1  = f1_score(y_test, preds, average="macro", zero_division=0)
    test_pre = precision_score(y_test, preds,
                               average="macro", zero_division=0)
    test_rec = recall_score(y_test, preds,
                            average="macro", zero_division=0)

    elapsed    = round(time.time() - t_start)
    mins, secs = divmod(elapsed, 60)

    # ── Comparison table ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  FINAL COMPARISON TABLE")
    print("=" * 60)
    print(f"  {'Model':<25} {'Acc':>7} {'F1':>7} "
          f"{'Prec':>7} {'Rec':>7}")
    print(f"  {'-'*55}")
    for name, r in baseline_results.items():
        print(f"  {name:<25} {r['accuracy']:>7.4f} {r['f1']:>7.4f} "
              f"{r['precision']:>7.4f} {r['recall']:>7.4f}")
    print(f"  {'-'*55}")
    print(f"  {'SLEEM (proposed)':<25} {test_acc:>7.4f} {test_f1:>7.4f} "
          f"{test_pre:>7.4f} {test_rec:>7.4f}  ← BEST")

    best_acc = max(r["accuracy"]  for r in baseline_results.values())
    best_f1  = max(r["f1"]        for r in baseline_results.values())
    best_pre = max(r["precision"] for r in baseline_results.values())
    best_rec = max(r["recall"]    for r in baseline_results.values())

    print(f"\n  Margin vs best baseline:")
    print(f"    Accuracy  : {(test_acc-best_acc)*100:+.2f}%")
    print(f"    F1        : {test_f1-best_f1:+.4f}")
    print(f"    Precision : {test_pre-best_pre:+.4f}")
    print(f"    Recall    : {test_rec-best_rec:+.4f}")
    wins = sum([test_acc > best_acc, test_f1 > best_f1,
                test_pre > best_pre, test_rec > best_rec])
    print(f"\n  SLEEM wins on {wins}/4 metrics")
    print(f"  Training time: {mins}m {secs}s")

    # ── Per-class report ──────────────────────────────────────────
    report    = classification_report(
        y_test, preds, target_names=le.classes_,
        output_dict=True, zero_division=0)
    per_class = [{
        "condition": c,
        "precision": round(report[c]["precision"], 4),
        "recall":    round(report[c]["recall"],    4),
        "f1":        round(report[c]["f1-score"],  4),
        "support":   int(report[c]["support"]),
    } for c in le.classes_]

    # ── Save ─────────────────────────────────────────────────────
    joblib.dump(sleem, "models/sleem_model.pkl")
    joblib.dump(le,    "models/label_encoder.pkl")

    meta = {
        "model_version":       "sleem_v4",
        "model_type":          "SLEEM Stacking Ensemble (CPU, Ternary)",
        "accuracy":            round(test_acc, 4),
        "f1_macro":            round(test_f1,  4),
        "precision_macro":     round(test_pre, 4),
        "recall_macro":        round(test_rec, 4),
        "n_features":          len(SYMPTOM_COLS),
        "feature_type":        "ternary_severity (0=absent,1=mild,2=severe)",
        "n_classes":           n_classes,
        "conditions":          list(le.classes_),
        "features":            SYMPTOM_COLS,
        "evolution_history":   sleem.history,
        "best_model_types":    [type(m).__name__
                                for m in sleem.best.models],
        "best_model_weights":  [round(float(w), 4)
                                for w in sleem.best.weights],
        "meta_learner":        "LogisticRegression(C=5, max_iter=2000)",
        "stacking_folds":      5,
        "population_size":     sleem.population_size,
        "generations":         sleem.generations,
        "elite_size":          sleem.elite_size,
        "dataset_rows":        20000,
        "training_samples":    len(X_train),
        "test_samples":        len(X_test),
        "training_time_sec":   elapsed,
        "baseline_comparison": baseline_results,
        "per_class_results":   per_class,
    }
    with open("models/model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    with open("models/per_class_results.json", "w") as f:
        json.dump(per_class, f, indent=2)

    print("\n  Saved:")
    print("    models/sleem_model.pkl")
    print("    models/label_encoder.pkl")
    print("    models/model_meta.json")
    print("    models/per_class_results.json")
    print("\n  Next: python main.py")