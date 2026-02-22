import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Dummy training dataset
data = {
    "fever": [1,0,1,0,1,0,1,0],
    "headache": [1,1,0,0,1,1,0,0],
    "fatigue": [1,0,1,0,1,0,1,0],
    "cough": [0,1,0,1,0,1,0,1],
    "risk": ["High","Low","High","Low","High","Low","High","Low"]
}

df = pd.DataFrame(data)

X = df[["fever","headache","fatigue","cough"]]
y = df["risk"]

model = RandomForestClassifier()
model.fit(X, y)

joblib.dump(model, "model.pkl")

print("Model trained and saved as model.pkl")