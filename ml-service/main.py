"""
MedPredict AI — Flask API
SLEEM v4 | Ternary severity input | Port 8000
"""
import os, warnings, logging
os.environ["LIGHTGBM_VERBOSITY"] = "-1"
warnings.filterwarnings("ignore")
logging.getLogger("lightgbm").setLevel(logging.ERROR)

import numpy as np
import joblib
import json
from flask import Flask, request, jsonify
from sleem_model import SLEEM, Individual

app = Flask(__name__)

sleem = joblib.load("models/sleem_model.pkl")
le    = joblib.load("models/label_encoder.pkl")
with open("models/model_meta.json") as f:
    meta = json.load(f)

FEATURES = meta["features"]

# Symptom name aliases -> canonical feature name
ALIASES = {
    "fever":"fever","headache":"headache","fatigue":"fatigue",
    "cough":"cough","chest pain":"chest_pain","chest_pain":"chest_pain",
    "shortness of breath":"shortness_of_breath",
    "shortness_of_breath":"shortness_of_breath",
    "breathlessness":"shortness_of_breath",
    "nausea":"nausea","dizziness":"dizziness",
    "sore throat":"sore_throat","sore_throat":"sore_throat",
    "throat irritation":"sore_throat",
    "body ache":"body_ache","body_ache":"body_ache",
    "muscle pain":"body_ache",
    "blurred vision":"blurred_vision","blurred_vision":"blurred_vision",
    "rapid heartbeat":"rapid_heartbeat","rapid_heartbeat":"rapid_heartbeat",
    "palpitations":"rapid_heartbeat","fast heart rate":"rapid_heartbeat",
    "chills":"chills",
    "loss of appetite":"loss_of_appetite",
    "loss_of_appetite":"loss_of_appetite",
    "insomnia":"insomnia","restlessness":"insomnia",
    "acidity":"acidity","heartburn":"acidity","acid reflux":"acidity",
    "indigestion":"indigestion",
    "stomach pain":"stomach_pain","stomach_pain":"stomach_pain",
    "abdominal pain":"stomach_pain","stomach ache":"stomach_pain",
    "vomiting":"vomiting","diarrhoea":"vomiting","diarrhea":"vomiting",
    "skin rash":"skin_rash","skin_rash":"skin_rash","rash":"skin_rash",
    "itching":"itching","skin irritation":"itching",
    "joint pain":"joint_pain","joint_pain":"joint_pain",
    "joint ache":"joint_pain",
    "sweating":"sweating","night sweats":"sweating",
    "excessive sweating":"sweating",
    "weight loss":"weight_loss","weight_loss":"weight_loss",
    "weight reduction":"weight_loss","losing weight":"weight_loss",
    "high fever":"fever","mild fever":"fever","low grade fever":"fever",
    "tired":"fatigue","tiredness":"fatigue","weakness":"fatigue",
}

# Severity word -> integer value
SEVERITY_WORDS = {
    "mild":1,"slight":1,"moderate":1,"low":1,
    "severe":2,"high":2,"extreme":2,"acute":2,"very":2,
}


def normalize(raw_symptoms):
    """
    Accepts:
      ["fever", "cough"]                        -> severity 2 (default)
      ["mild fever", "severe cough"]            -> parsed from name
      [{"symptom":"fever","severity":2}, ...]   -> explicit severity
    Returns: feature vector, matched list, unmatched list
    """
    vec       = {f: 0 for f in FEATURES}
    matched   = []
    unmatched = []

    for item in raw_symptoms:
        if isinstance(item, dict):
            name     = str(item.get("symptom", ""))
            severity = int(item.get("severity", 2))
        else:
            name     = str(item)
            severity = 2
            # Check if severity word is embedded in name
            name_lower = name.lower().strip()
            for word, val in SEVERITY_WORDS.items():
                if name_lower.startswith(word + " ") or \
                   name_lower.endswith(" " + word):
                    severity = val
                    name_lower = name_lower.replace(word, "").strip()
                    break
            name = name_lower

        key   = name.lower().strip()
        canon = ALIASES.get(key)
        if canon and canon in vec:
            vec[canon] = max(vec[canon], severity)
            matched.append(canon)
        else:
            unmatched.append(str(item))

    arr = np.array([vec[f] for f in FEATURES]).reshape(1, -1)
    return arr, matched, unmatched


def severity_score(count):
    return max(1, min(5, -(-count // 3)))


def risk_label(s):
    return {1:"Low",2:"Low",3:"Medium",4:"Medium",5:"High"}[s]


@app.route("/predict", methods=["POST"])
def predict():
    data              = request.get_json(force=True)
    raw               = data.get("symptoms", [])
    vec, matched, unk = normalize(raw)
    count             = int((vec > 0).sum())
    sev               = severity_score(count)

    if count < 3:
        return jsonify({
            "condition":             "Inconclusive",
            "risk":                  "Unknown",
            "confidence":            0.0,
            "confidence_margin":     0.0,
            "severity_score":        sev,
            "important_factors":     matched,
            "unrecognized_symptoms": unk,
            "top_predictions":       [],
            "model_version":         meta["model_version"],
            "reason":                f"{count} symptom(s) found. "
                                     "Minimum 3 required."
        })

    probs      = sleem.predict_proba(vec)[0]
    top_idx    = np.argsort(probs)[::-1]
    condition  = le.classes_[top_idx[0]]
    confidence = float(probs[top_idx[0]])
    margin     = float(probs[top_idx[0]] - probs[top_idx[1]]) \
                 if len(top_idx) > 1 else 1.0

    if confidence < 0.20 or margin < 0.05:
        condition = "Inconclusive"

    return jsonify({
        "condition":             condition,
        "risk":                  risk_label(sev),
        "confidence":            round(confidence, 4),
        "confidence_margin":     round(margin, 4),
        "severity_score":        sev,
        "important_factors":     matched,
        "unrecognized_symptoms": unk,
        "top_predictions": [
            {"condition":   le.classes_[i],
             "probability": round(float(probs[i]), 4)}
            for i in top_idx[:3]
        ],
        "model_version": meta["model_version"]
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":        "ok",
        "model":         meta["model_version"],
        "accuracy":      meta["accuracy"],
        "f1_macro":      meta["f1_macro"],
        "precision":     meta.get("precision_macro"),
        "recall":        meta.get("recall_macro"),
        "conditions":    meta["n_classes"],
        "features":      meta["n_features"],
        "feature_type":  meta.get("feature_type"),
        "meta_learner":  meta.get("meta_learner"),
        "stacking_folds":meta.get("stacking_folds"),
    })


@app.route("/conditions", methods=["GET"])
def conditions():
    return jsonify({
        "conditions": list(le.classes_),
        "total":      len(le.classes_)
    })


@app.route("/symptoms", methods=["GET"])
def symptoms():
    return jsonify({
        "symptoms":        FEATURES,
        "total":           len(FEATURES),
        "severity_levels": {
            "0": "absent",
            "1": "mild",
            "2": "severe"
        },
        "usage_tip": (
            "Send symptoms as strings (e.g. 'fever') for severity 2, "
            "'mild fever' for severity 1, or as dicts "
            "{\"symptom\":\"fever\",\"severity\":2} for explicit control."
        )
    })


if __name__ == "__main__":
    print("=" * 50)
    print(f"  MedPredict AI — SLEEM {meta['model_version']}")
    print(f"  Accuracy  : {meta['accuracy']*100:.2f}%")
    print(f"  Macro F1  : {meta['f1_macro']:.4f}")
    print(f"  Classes   : {meta['n_classes']}")
    print(f"  Features  : {meta['n_features']} (ternary severity)")
    print(f"  API       : http://localhost:8000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=8000, debug=False)