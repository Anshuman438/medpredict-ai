from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import joblib
import pandas as pd

app = FastAPI(title="MedPredict ML Service")

# Load trained pipeline
pipeline = joblib.load("model.pkl")

# Extract feature importance from model
model = pipeline.named_steps["model"]
feature_importances = model.feature_importances_

# Feature configuration
FEATURES = [
    "fever",
    "headache",
    "fatigue",
    "cough",
    "chest_pain",
    "dizziness"
]

MAPPING = {
    "Fever": "fever",
    "Headache": "headache",
    "Fatigue": "fatigue",
    "Cough": "cough",
    "Chest Pain": "chest_pain",
    "Dizziness": "dizziness"
}

# Request Schema
class SymptomInput(BaseModel):
    symptoms: List[str]

@app.get("/")
def root():
    return {"message": "MedPredict ML Service Running"}

@app.post("/predict")
def predict(input: SymptomInput):

    # Initialize feature vector
    feature_map = {feature: 0 for feature in FEATURES}

    # Map symptoms to features
    for symptom in input.symptoms:
        if symptom in MAPPING:
            feature_map[MAPPING[symptom]] = 1

    # Convert to DataFrame
    df = pd.DataFrame([feature_map])

    # Predict condition
    condition = pipeline.predict(df)[0]

    # Probability confidence
    probabilities = pipeline.predict_proba(df)[0]
    confidence_value = max(probabilities) * 100

    # Risk classification
    if confidence_value > 80:
        risk = "High"
    elif confidence_value > 50:
        risk = "Medium"
    else:
        risk = "Low"

    # Severity score (scaled)
    severity_score = round(confidence_value / 20, 2)

    # Explainable AI (important contributing features)
    importance_list = []

    for feature, importance in zip(FEATURES, feature_importances):
        if feature_map[feature] == 1:
            importance_list.append({
                "feature": feature,
                "impact": round(float(importance), 4)
            })

    importance_list = sorted(
        importance_list,
        key=lambda x: x["impact"],
        reverse=True
    )

    return {
        "condition": condition,
        "risk": risk,
        "confidence": f"{confidence_value:.2f}%",
        "severity_score": severity_score,
        "important_factors": importance_list,
        "model_version": "v4.0"
    }