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

# Maps UI label -> feature index and severity
# UI sends symptom names; we map to severity 2 (severe) by default
# User can optionally send {"symptom": "fever", "severity": 1} for mild

ALIASES = {
    "fever":"fever","headache":"headache","fatigue":"fatigue",
    "cough":"cough","chest pain":"chest_pain","chest_pain":"chest_pain",
    "shortness of breath":"shortness_of_breath",
    "shortness_of_breath":"shortness_of_breath",
    "breathlessness":"shortness_of_breath",
    "nausea":"nausea","dizziness":"dizziness",
    "sore throat":"sore_throat","sore_throat":"sore_throat",
    "body ache":"body_ache","body_ache":"body_ache",
    "blurred vision":"blurred_vision","blurred_vision":"blurred_vision",
    "rapid heartbeat":"rapid_heartbeat","rapid_heartbeat":"rapid_heartbeat",
    "palpitations":"rapid_heartbeat","chills":"chills",
    "loss of appetite":"loss_of_appetite","loss_of_appetite":"loss_of_appetite",
    "insomnia":"insomnia","acidity":"acidity","indigestion":"indigestion",
    "stomach pain":"stomach_pain","stomach_pain":"stomach_pain",
    "vomiting":"vomiting","skin rash":"skin_rash","skin_rash":"skin_rash",
    "rash":"skin_rash","itching":"itching",
    "joint pain":"joint_pain","joint_pain":"joint_pain",
    "sweating":"sweating","weight loss":"weight_loss","weight_loss":"weight_loss",
    "high fever":"fever","mild fever":"fever","low fever":"fever",
    "tired":"fatigue","tiredness":"fatigue","weakness":"fatigue",
    "muscle pain":"body_ache","throat irritation":"sore_throat",
    "heartburn":"acidity","acid reflux":"acidity",
    "stomach ache":"stomach_pain","abdominal pain":"stomach_pain",
    "loose motion":"vomiting","diarrhoea":"vomiting","diarrhea":"vomiting",
    "skin irritation":"itching","joint ache":"joint_pain",
    "excessive sweating":"sweating","night sweats":"sweating",
    "weight reduction":"weight_loss","losing weight":"weight_loss",
}


def normalize(raw_symptoms):
    """
    Accepts either:
      ["Fever", "Headache"]              -> all severity 2
      [{"symptom":"Fever","severity":2}] -> explicit severity
    """
    vec = {f: 0 for f in FEATURES}
    matched = []
    unmatched = []

    for item in raw_symptoms:
        if isinstance(item, dict):
            name     = item.get("symptom", "")
            severity = int(item.get("severity", 2))
        else:
            name     = str(item)
            severity = 2   # default: severe when just a name is sent

        key   = name.lower().strip()
        canon = ALIASES.get(key)
        if canon and canon in vec:
            vec[canon] = max(vec[canon], severity)  # take highest severity
            matched.append(canon)
        else:
            unmatched.append(name)

    arr = np.array([vec[f] for f in FEATURES]).reshape(1, -1)
    return arr, matched, unmatched


def severity_score(count):
    return max(1, min(5, -(-count // 3)))


def risk_label(s):
    return {1:"Low",2:"Low",3:"Medium",4:"Medium",5:"High"}[s]


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)
    raw  = data.get("symptoms", [])

    vec, matched, unmatched = normalize(raw)
    count = int((vec > 0).sum())   # count present symptoms (any severity)
    sev   = severity_score(count)

    if count < 3:
        return jsonify({
            "condition":             "Inconclusive",
            "risk":                  "Unknown",
            "confidence":            0.0,
            "confidence_margin":     0.0,
            "severity_score":        sev,
            "important_factors":     matched,
            "unrecognized_symptoms": unmatched,
            "top_predictions":       [],
            "model_version":         meta["model_version"],
            "reason":                f"Only {count} symptom(s) recognized. Minimum 3 required."
        })

    probs      = sleem.predict_proba(vec)[0]
    sorted_idx = np.argsort(probs)[::-1]
    condition  = le.classes_[sorted_idx[0]]
    confidence = float(probs[sorted_idx[0]])
    margin     = float(probs[sorted_idx[0]] - probs[sorted_idx[1]]) \
                 if len(sorted_idx) > 1 else 1.0

    if confidence < 0.20 or margin < 0.05:
        condition = "Inconclusive"

    return jsonify({
        "condition":             condition,
        "risk":                  risk_label(sev),
        "confidence":            round(confidence, 4),
        "confidence_margin":     round(margin, 4),
        "severity_score":        sev,
        "important_factors":     matched,
        "unrecognized_symptoms": unmatched,
        "top_predictions": [
            {"condition":   le.classes_[i],
             "probability": round(float(probs[i]), 4)}
            for i in sorted_idx[:3]
        ],
        "model_version": meta["model_version"]
    })


@app.route("/health",     methods=["GET"])
def health():
    return jsonify({
        "status":     "ok",
        "model":      meta["model_version"],
        "accuracy":   meta["accuracy"],
        "f1_macro":   meta["f1_macro"],
        "conditions": meta["n_classes"],
        "features":   meta["n_features"],
        "meta_learner": meta.get("meta_learner","N/A")
    })

@app.route("/conditions", methods=["GET"])
def conditions():
    return jsonify({"conditions": list(le.classes_), "total": len(le.classes_)})

@app.route("/symptoms",   methods=["GET"])
def symptoms_list():
    return jsonify({"symptoms": FEATURES, "total": len(FEATURES),
                    "severity_levels": {"0":"absent","1":"mild","2":"severe"}})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)