import numpy as np
import pandas as pd
import random, joblib, json, os, warnings
warnings.filterwarnings("ignore")

from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from sleem_model import SLEEM
from generate_dataset import generate, SYMPTOM_COLS

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
FEATURES = SYMPTOM_COLS

OLD_COLS = [
    "fever","headache","fatigue","cough","chest_pain",
    "shortness_of_breath","nausea","dizziness","sore_throat",
    "body_ache","blurred_vision","rapid_heartbeat","chills",
    "loss_of_appetite","insomnia"
]
NEW_9 = ["acidity","indigestion","stomach_pain","vomiting",
         "skin_rash","itching","joint_pain","sweating","weight_loss"]


def detect_gpu():
    try:
        import xgboost as xgb
        test = xgb.XGBClassifier(tree_method="hist", device="cuda", n_estimators=1)
        import numpy as np
        test.fit(np.random.rand(10,4), np.array([0]*5+[1]*5))
        print("  GPU detected — using CUDA acceleration")
        return True
    except Exception:
        print("  No GPU detected — using CPU")
        return False


def load_csv(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    target = next((c for c in ["prognosis","condition"] if c in df.columns), None)
    y = df[target].dropna()
    y = y[y.str.strip() != ""]
    X = pd.DataFrame({f: df[f].fillna(0).astype(int) if f in df.columns else 0
                      for f in FEATURES})
    return X.loc[y.index].values, y.values


if __name__ == "__main__":
    print("=" * 54)
    print("  SLEEM v3 — Stacking + Severity Features + GPU")
    print("=" * 54)

    os.makedirs("datasets", exist_ok=True)
    os.makedirs("models",   exist_ok=True)

    # Step 1: Detect GPU
    print("\n[0/4] Checking GPU...")
    use_gpu = detect_gpu()

    # Step 2: Generate severity-based dataset
    print("\n[1/4] Generating severity dataset (50,000 rows)...")
    syn_path = "datasets/synthetic_training_data.csv"
    generate(syn_path, n_samples=50000)

    frames = [pd.read_csv(syn_path)]
    data_path = "datasets/final_training_data.csv"
    merged = pd.concat(frames, ignore_index=True)
    merged = merged.sample(frac=1, random_state=SEED).reset_index(drop=True)
    merged.to_csv(data_path, index=False)
    print(f"  Dataset: {len(merged)} rows | {merged['prognosis'].nunique()} classes")

    # Step 3: Load and encode
    print("\n[2/4] Loading data...")
    X, y_raw = load_csv(data_path)
    le = LabelEncoder()
    y  = le.fit_transform(y_raw)
    print(f"  Samples: {len(X)} | Features: {X.shape[1]} | Classes: {len(le.classes_)}")
    print(f"  Feature range: {X.min()} - {X.max()} (0=absent, 1=mild, 2=severe)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)
    print(f"  Train: {len(X_train)} | Test: {len(X_test)}")

    # Step 4: Train SLEEM with stacking
    print("\n[3/4] Training SLEEM (stacking + meta-learner)...")
    print("  Config: pop=10, gen=10, elite=3, meta=LogisticRegression")
    sleem = SLEEM(
        population_size=10,
        generations=10,
        elite_size=3,
        use_gpu=use_gpu
    )
    sleem.fit(X_train, y_train)

    # Step 5: Evaluate
    print("\n[4/4] Final evaluation...")
    preds    = sleem.predict(X_test)
    test_acc = accuracy_score(y_test, preds)
    test_f1  = f1_score(y_test, preds, average="macro", zero_division=0)
    print(f"  Test Accuracy : {test_acc*100:.2f}%")
    print(f"  Test Macro F1 : {test_f1:.4f}")

    # Confidence check
    probs   = sleem.predict_proba(X_test[:20])
    confs   = [p.max() for p in probs]
    margins = [sorted(p)[-1]-sorted(p)[-2] for p in probs]
    inconc  = sum(1 for c,m in zip(confs,margins) if c<0.20 or m<0.05)
    print(f"  Avg confidence : {np.mean(confs):.3f}")
    print(f"  Inconclusive/20: {inconc}/20")

    joblib.dump(sleem, "models/sleem_model.pkl")
    joblib.dump(le,    "models/label_encoder.pkl")

    meta = {
        "model_version":      "sleem_v3",
        "model_type":         "SLEEM with Stacking Meta-Learner",
        "accuracy":           round(test_acc, 4),
        "f1_macro":           round(test_f1, 4),
        "n_features":         len(FEATURES),
        "feature_type":       "ternary (0=absent, 1=mild, 2=severe)",
        "n_classes":          len(le.classes_),
        "conditions":         list(le.classes_),
        "features":           FEATURES,
        "evolution_history":  sleem.history,
        "best_model_types":   [type(m).__name__ for m in sleem.best.models],
        "best_model_weights": [round(float(w),4) for w in sleem.best.weights],
        "meta_learner":       "LogisticRegression",
        "population_size":    sleem.population_size,
        "generations":        sleem.generations,
        "gpu_used":           use_gpu,
        "training_samples":   len(X_train),
        "test_samples":       len(X_test),
    }
    with open("models/model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print("\n  Saved: models/sleem_model.pkl | label_encoder.pkl | model_meta.json")
    print(f"  Best models  : {meta['best_model_types']}")
    print(f"  Meta-learner : {meta['meta_learner']}")
    print(f"  GPU used     : {use_gpu}")
    print(f"\n  Final: {test_acc*100:.2f}% accuracy")
    print("  Training complete. Run: python main.py")