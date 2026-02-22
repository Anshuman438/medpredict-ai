from fastapi import FastAPI
import joblib
import pandas as pd
from pydantic import BaseModel
from typing import List

app = FastAPI()

model = joblib.load("model.pkl")

class SymptomInput(BaseModel):
    symptoms: List[str]

FEATURES = ["fever", "headache", "fatigue", "cough"]

@app.get("/")
def root():
    return {"message": "ML Service Running"}

@app.post("/predict")
def predict(input: SymptomInput):
    feature_map = {feature: 0 for feature in FEATURES}

    mapping = {
        "Fever": "fever",
        "Headache": "headache",
        "Fatigue": "fatigue",
        "Cough": "cough"
    }

    for symptom in input.symptoms:
        if symptom in mapping:
            feature_map[mapping[symptom]] = 1

    df = pd.DataFrame([feature_map])

    prediction = model.predict(df)[0]
    probabilities = model.predict_proba(df)[0]

    confidence = max(probabilities) * 100

    return {
        "condition": "Hypertension",
        "risk": prediction,
        "confidence": f"{confidence:.2f}%",
        "model_version": "v1.0"
    }