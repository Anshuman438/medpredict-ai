# main.py — Flask API (SLEEM)
import numpy as np
import joblib
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# ── Load artefacts ────────────────────────────────────────────────
sleem = joblib.load("sleem_model.pkl")
le    = joblib.load("label_encoder.pkl")
with open("model_meta.json") as f:
    meta = json.load(f)

# 24 frontend feature names (saved by train_model.py)
FEATURES = meta["features"]

# ── Frontend label → canonical feature key ───────────────────────
# Maps whatever the frontend sends (button label / slug) to the exact
# feature key used during training.  Add more aliases freely.
SYMPTOM_ALIASES = {
    # Fever
    "fever":                 "fever",
    "high fever":            "fever",
    "mild fever":            "fever",
    # Headache
    "headache":              "headache",
    "head pain":             "headache",
    # Fatigue
    "fatigue":               "fatigue",
    "tired":                 "fatigue",
    "tiredness":             "fatigue",
    "lethargy":              "fatigue",
    "malaise":               "fatigue",
    # Cough
    "cough":                 "cough",
    "phlegm":                "cough",
    "blood in sputum":       "cough",
    # Chest pain
    "chest pain":            "chest_pain",
    "chest_pain":            "chest_pain",
    # Shortness of breath
    "shortness of breath":   "shortness_of_breath",
    "breathlessness":        "shortness_of_breath",
    "shortness_of_breath":   "shortness_of_breath",
    # Nausea / vomiting
    "nausea":                "nausea",
    "vomiting":              "vomiting",
    # Dizziness
    "dizziness":             "dizziness",
    "dizzy":                 "dizziness",
    "vertigo":               "dizziness",
    "spinning":              "dizziness",
    # Sore throat
    "sore throat":           "sore_throat",
    "sore_throat":           "sore_throat",
    "throat irritation":     "sore_throat",
    # Body ache
    "body ache":             "body_ache",
    "body_ache":             "body_ache",
    "muscle pain":           "body_ache",
    "back pain":             "body_ache",
    "neck pain":             "body_ache",
    # Blurred vision
    "blurred vision":        "blurred_vision",
    "blurred_vision":        "blurred_vision",
    "visual disturbances":   "blurred_vision",
    # Rapid heartbeat
    "rapid heartbeat":       "rapid_heartbeat",
    "rapid_heartbeat":       "rapid_heartbeat",
    "palpitations":          "rapid_heartbeat",
    "fast heart rate":       "rapid_heartbeat",
    # Chills
    "chills":                "chills",
    "shivering":             "chills",
    # Loss of appetite
    "loss of appetite":      "loss_of_appetite",
    "no appetite":           "loss_of_appetite",
    "loss_of_appetite":      "loss_of_appetite",
    # Insomnia
    "insomnia":              "insomnia",
    "restlessness":          "insomnia",
    "poor concentration":    "insomnia",
    # Acidity
    "acidity":               "acidity",
    "acid reflux":           "acidity",
    # Indigestion
    "indigestion":           "indigestion",
    "gas":                   "indigestion",
    "flatulence":            "indigestion",
    # Stomach pain
    "stomach pain":          "stomach_pain",
    "stomach_pain":          "stomach_pain",
    "abdominal pain":        "stomach_pain",
    "belly pain":            "stomach_pain",
    # Skin rash
    "skin rash":             "skin_rash",
    "skin_rash":             "skin_rash",
    "rash":                  "skin_rash",
    "blisters":              "skin_rash",
    "pimples":               "skin_rash",
    # Itching
    "itching":               "itching",
    "itch":                  "itching",
    "internal itching":      "itching",
    # Joint pain
    "joint pain":            "joint_pain",
    "joint_pain":            "joint_pain",
    "knee pain":             "joint_pain",
    "hip pain":              "joint_pain",
    "swollen joints":        "joint_pain",
    # Sweating
    "sweating":              "sweating",
    "excessive sweating":    "sweating",
    # Weight loss
    "weight loss":           "weight_loss",
    "weight_loss":           "weight_loss",
    "weight gain":           "weight_loss",
}


def normalize_symptoms(raw_symptoms):
    """Map incoming symptom strings to the 24-feature binary vector."""
    vector  = {f: 0 for f in FEATURES}
    matched = []
    for s in raw_symptoms:
        key = s.lower().strip()
        # 1) alias map
        canonical = SYMPTOM_ALIASES.get(key)
        # 2) direct key match (frontend sends slugs like "chest_pain")
        if canonical is None and key in vector:
            canonical = key
        if canonical and canonical in vector:
            vector[canonical] = 1
            matched.append(canonical)
    return np.array([vector[f] for f in FEATURES]).reshape(1, -1), matched


def severity_score(symptom_count):
    return max(1, min(5, -(-symptom_count // 3)))


def risk_label(score):
    if score <= 2: return "Low"
    if score <= 4: return "Medium"
    return "High"


# ── /predict ──────────────────────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict():
    data         = request.get_json()
    raw_symptoms = data.get("symptoms", [])

    feature_vector, matched = normalize_symptoms(raw_symptoms)
    symptom_count = int(feature_vector.sum())

    MIN_SYMPTOMS   = 2
    MIN_CONFIDENCE = 0.20
    MIN_MARGIN     = 0.05

    if symptom_count < MIN_SYMPTOMS:
        return jsonify({
            "condition":         "Inconclusive",
            "risk":              "Unknown",
            "confidence":        0.0,
            "confidence_margin": 0.0,
            "severity_score":    severity_score(symptom_count),
            "important_factors": matched,
            "top_predictions":   [],
            "model_version":     meta["model_version"],
            "reason":            f"Please select at least {MIN_SYMPTOMS} symptoms",
        })

    probs      = sleem.predict_proba(feature_vector)[0]
    sorted_idx = np.argsort(probs)[::-1]

    top_condition = le.classes_[sorted_idx[0]]
    confidence    = float(probs[sorted_idx[0]])
    margin        = float(probs[sorted_idx[0]] - probs[sorted_idx[1]]) if len(sorted_idx) > 1 else 1.0

    if confidence < MIN_CONFIDENCE or margin < MIN_MARGIN:
        top_condition = "Inconclusive"

    top_predictions = [
        {"condition": le.classes_[i], "probability": round(float(probs[i]), 4)}
        for i in sorted_idx[:3]
    ]

    sev = severity_score(symptom_count)

    return jsonify({
        "condition":         top_condition,
        "risk":              risk_label(sev),
        "confidence":        round(confidence, 4),
        "confidence_margin": round(margin, 4),
        "severity_score":    sev,
        "important_factors": matched,
        "top_predictions":   top_predictions,
        "model_version":     meta["model_version"],
    })


# ── /health ───────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":     "ok",
        "model":      meta["model_version"],
        "accuracy":   meta["accuracy"],
        "conditions": meta["n_classes"],
        "features":   meta["n_features"],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)