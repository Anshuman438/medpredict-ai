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

OLD_COLS = [
    "fever","headache","fatigue","cough","chest_pain",
    "shortness_of_breath","nausea","dizziness","sore_throat",
    "body_ache","blurred_vision","rapid_heartbeat","chills",
    "loss_of_appetite","insomnia"
]
NEW_9 = ["acidity","indigestion","stomach_pain","vomiting",
         "skin_rash","itching","joint_pain","sweating","weight_loss"]

def expand_old(path):
    """Load a 15-col CSV, add 9 zero columns, return 24-col df."""
    try:
        df = pd.read_csv(path)
    except Exception:
        return None
    df.columns = df.columns.str.lower().str.replace(" ","_")
    target = next((c for c in ["prognosis","condition"] if c in df.columns), None)
    if not target:
        # headerless — assign column names
        df = pd.read_csv(path, header=None)
        if df.shape[1] == 16:
            df.columns = OLD_COLS + ["prognosis"]
        else:
            return None
        target = "prognosis"
    df = df.rename(columns={target:"prognosis"})
    for col in NEW_9:
        df[col] = 0
    df = df[SYMPTOM_COLS + ["prognosis"]]
    df = df[df["prognosis"].notna() & (df["prognosis"].str.strip() != "")]
    df[SYMPTOM_COLS] = df[SYMPTOM_COLS].fillna(0).astype(int)
    df["prognosis"] = df["prognosis"].str.strip()
    print(f"  Loaded {path}: {len(df)} rows, {df['prognosis'].nunique()} classes")
    return df

def load_csv(path):
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower().str.replace(" ","_")
    target = next((c for c in ["prognosis","condition"] if c in df.columns), None)
    y = df[target].dropna()
    y = y[y.str.strip() != ""]
    X = pd.DataFrame({f: df[f].fillna(0).astype(int) if f in df.columns else 0
                      for f in SYMPTOM_COLS})
    return X.loc[y.index].values, y.values

if __name__ == "__main__":
    print("="*52)
    print("  SLEEM Training Pipeline  (24 features, 20000 rows)")
    print("="*52)

    os.makedirs("datasets", exist_ok=True)
    os.makedirs("models",   exist_ok=True)

    # ── Step 1: Build dataset ──────────────────────────────────
    print("\n[1/4] Building dataset...")
    syn_path = "datasets/synthetic_training_data.csv"
    generate(syn_path, n_samples=20000)

    frames = [pd.read_csv(syn_path)]

    for old in ["datasets/Training.csv", "datasets/Testing.csv"]:
        if os.path.exists(old):
            df = expand_old(old)
            if df is not None:
                frames.append(df)

    merged = pd.concat(frames, ignore_index=True).drop_duplicates()
    merged = merged.sample(frac=1, random_state=SEED).reset_index(drop=True)
    data_path = "datasets/final_training_data.csv"
    merged.to_csv(data_path, index=False)
    print(f"  Final dataset: {len(merged)} rows, {merged['prognosis'].nunique()} classes")

    # ── Step 2: Load ───────────────────────────────────────────
    print("\n[2/4] Loading data...")
    X, y_raw = load_csv(data_path)
    le = LabelEncoder()
    y  = le.fit_transform(y_raw)
    print(f"  Samples: {len(X)} | Features: {X.shape[1]} | Classes: {len(le.classes_)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y)
    print(f"  Train: {len(X_train)} | Test: {len(X_test)}")

    # ── Step 3: Train ──────────────────────────────────────────
    print("\n[3/4] Starting SLEEM evolution...")
    sleem = SLEEM(population_size=10, generations=8, elite_size=3)
    sleem.fit(X_train, y_train)

    # ── Step 4: Evaluate & save ────────────────────────────────
    print("\n[4/4] Evaluating on test set...")
    preds    = sleem.predict(X_test)
    test_acc = accuracy_score(y_test, preds)
    test_f1  = f1_score(y_test, preds, average="macro", zero_division=0)
    print(f"  Test Accuracy : {test_acc*100:.2f}%")
    print(f"  Test Macro F1 : {test_f1:.4f}")

    # Confidence sanity check
    probs = sleem.predict_proba(X_test[:20])
    confs = [p.max() for p in probs]
    margins = [sorted(p)[-1]-sorted(p)[-2] for p in probs]
    print(f"  Avg confidence on 20 samples: {np.mean(confs):.3f}")
    print(f"  Avg margin    on 20 samples: {np.mean(margins):.3f}")
    inconclusive_count = sum(1 for c,m in zip(confs,margins) if c<0.33 or m<0.08)
    print(f"  Inconclusive on 20 samples: {inconclusive_count}/20")

    joblib.dump(sleem, "models/sleem_model.pkl")
    joblib.dump(le,    "models/label_encoder.pkl")
    meta = {
        "model_version":      "sleem_v1",
        "model_type":         "Self-Learning Evolutionary Ensemble Model",
        "accuracy":           round(test_acc,4),
        "f1_macro":           round(test_f1,4),
        "n_features":         len(SYMPTOM_COLS),
        "n_classes":          len(le.classes_),
        "conditions":         list(le.classes_),
        "features":           SYMPTOM_COLS,
        "evolution_history":  sleem.history,
        "best_model_types":   [type(m).__name__ for m in sleem.best.models],
        "best_model_weights": [round(float(w),4) for w in sleem.best.weights],
        "population_size":    sleem.population_size,
        "generations":        sleem.generations,
        "training_samples":   len(X_train),
        "test_samples":       len(X_test),
    }
    with open("models/model_meta.json","w") as f:
        json.dump(meta, f, indent=2)

    print("\n  Saved: models/sleem_model.pkl | label_encoder.pkl | model_meta.json")
    print(f"  Best models : {meta['best_model_types']}")
    print(f"  Best weights: {meta['best_model_weights']}")
    print("\n  Training complete. Run: python main.py")