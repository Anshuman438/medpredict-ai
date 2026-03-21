# train_model.py — SLEEM Training Script
import numpy as np
import pandas as pd
import random
import joblib
import json
from sklearn.metrics import accuracy_score, f1_score
from sklearn.preprocessing import LabelEncoder

from sleem_model import SLEEM

# ── Reproducibility ──────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── Frontend symptom → dataset columns mapping ───────────────────
# Each of the 24 UI buttons maps to ALL related columns in the CSV.
# This is the key bridge: simple UX ↔ rich 132-feature model signal.
SYMPTOM_MAP = {
    "fever":               ["high_fever", "mild_fever"],
    "headache":            ["headache"],
    "fatigue":             ["fatigue", "lethargy", "malaise"],
    "cough":               ["cough", "phlegm", "mucoid_sputum", "rusty_sputum", "blood_in_sputum"],
    "chest_pain":          ["chest_pain"],
    "shortness_of_breath": ["breathlessness"],
    "nausea":              ["nausea", "vomiting"],
    "dizziness":           ["dizziness", "spinning_movements", "loss_of_balance", "unsteadiness"],
    "sore_throat":         ["throat_irritation", "patches_in_throat"],
    "body_ache":           ["muscle_pain", "joint_pain", "knee_pain", "hip_joint_pain",
                            "neck_pain", "back_pain", "muscle_weakness", "weakness_in_limbs"],
    "blurred_vision":      ["blurred_and_distorted_vision", "visual_disturbances"],
    "rapid_heartbeat":     ["fast_heart_rate", "palpitations"],
    "chills":              ["chills", "shivering"],
    "loss_of_appetite":    ["loss_of_appetite"],
    "insomnia":            ["restlessness", "lack_of_concentration"],
    "acidity":             ["acidity", "indigestion"],
    "indigestion":         ["indigestion", "acidity", "passage_of_gases",
                            "stomach_pain", "abdominal_pain", "belly_pain"],
    "stomach_pain":        ["stomach_pain", "abdominal_pain", "belly_pain",
                            "distention_of_abdomen", "swelling_of_stomach"],
    "vomiting":            ["vomiting", "nausea"],
    "skin_rash":           ["skin_rash", "itching", "nodal_skin_eruptions",
                            "dischromic__patches", "red_spots_over_body", "skin_peeling",
                            "silver_like_dusting", "blister", "pus_filled_pimples",
                            "blackheads", "yellow_crust_ooze", "red_sore_around_nose",
                            "inflammatory_nails"],
    "itching":             ["itching", "skin_rash", "internal_itching"],
    "joint_pain":          ["joint_pain", "knee_pain", "hip_joint_pain",
                            "swelling_joints", "movement_stiffness", "painful_walking"],
    "sweating":            ["sweating"],
    "weight_loss":         ["weight_loss", "weight_gain"],
}

FEATURES = list(SYMPTOM_MAP.keys())   # 24 frontend features


def clean_df(df):
    df = df.copy()
    df.columns = (
        df.columns
        .str.lower()
        .str.strip()
        .str.replace(" ", "_")
        .str.replace(r"[^a-z0-9_]", "_", regex=True)
    )
    return df


def build_features(df, symptom_map):
    """Collapse raw dataset columns into the 24 frontend features via OR (max)."""
    X = pd.DataFrame()
    for feature, sources in symptom_map.items():
        available = [s for s in sources if s in df.columns]
        X[feature] = df[available].max(axis=1).fillna(0).astype(int) if available else 0
    return X


def load_data(path="datasets/Training.csv"):
    df = clean_df(pd.read_csv(path))
    target_col = next((c for c in ["prognosis", "condition"] if c in df.columns), None)
    if not target_col:
        raise ValueError("No target column found")

    y_raw = df[target_col].dropna()
    X     = build_features(df, SYMPTOM_MAP).loc[y_raw.index]

    active = X.sum(axis=1)
    print(f"   Avg active features/sample : {active.mean():.2f}")
    print(f"   Samples with ≥2 features   : {(active >= 2).sum()} / {len(X)}")

    le = LabelEncoder()
    y  = le.fit_transform(y_raw)
    return X.values, y, le


def load_test(path, le):
    df = clean_df(pd.read_csv(path))
    target_col = next((c for c in ["prognosis", "condition"] if c in df.columns), None)
    X = build_features(df, SYMPTOM_MAP)
    y = le.transform(df[target_col])
    return X.values, y


if __name__ == "__main__":
    print("📦 Loading training data...")
    X, y, le = load_data("datasets/Training.csv")
    print(f"   Samples : {len(X)} | Features: {X.shape[1]} | Classes: {len(le.classes_)}")

    # ⚠️  TEST MODE — use population_size=10, generations=8 for production
    print("\n🧬 Starting SLEEM Evolution  [TEST MODE: pop=4, gen=3]...")
    sleem = SLEEM(population_size=4, generations=3, elite_size=2)
    sleem.fit(X, y)

    print("\n📊 Evaluating on test set...")
    X_test, y_test = load_test("datasets/Testing.csv", le)
    test_preds = sleem.predict(X_test)
    test_acc   = accuracy_score(y_test, test_preds)
    test_f1    = f1_score(y_test, test_preds, average="macro", zero_division=0)
    print(f"   Test Accuracy : {test_acc:.4f}")
    print(f"   Test F1 macro : {test_f1:.4f}")

    joblib.dump(sleem, "sleem_model.pkl")
    joblib.dump(le,    "label_encoder.pkl")

    meta = {
        "model_version":           "sleem_v1",
        "model_type":              "Self-Learning Evolutionary Ensemble",
        "accuracy":                round(test_acc, 4),
        "f1_macro":                round(test_f1, 4),
        "n_features":              len(FEATURES),
        "n_classes":               len(le.classes_),
        "conditions":              list(le.classes_),
        "features":                FEATURES,
        "symptom_map":             SYMPTOM_MAP,
        "evolution_history":       sleem.history,
        "best_individual_models":  [type(m).__name__ for m in sleem.best.models],
        "best_individual_weights": sleem.best.weights.tolist(),
    }
    with open("model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print("\n✅ Saved: sleem_model.pkl | label_encoder.pkl | model_meta.json")