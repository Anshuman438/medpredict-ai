import numpy as np
import pandas as pd
import random
import os

random.seed(42)
np.random.seed(42)

SYMPTOM_COLS = [
    "fever","headache","fatigue","cough","chest_pain",
    "shortness_of_breath","nausea","dizziness","sore_throat",
    "body_ache","blurred_vision","rapid_heartbeat","chills",
    "loss_of_appetite","insomnia","acidity","indigestion",
    "stomach_pain","vomiting","skin_rash","itching",
    "joint_pain","sweating","weight_loss"
]

# Severity: 0=absent  1=mild  2=severe
CONDITIONS = {
    "Vertigo Paroxysmal Positional":  {"primary":[7,6],       "secondary":[1,10,22]},
    "AIDS":                           {"primary":[2,23,13],   "secondary":[0,9,12,19]},
    "Acne":                           {"primary":[19,20],     "secondary":[14,2]},
    "Alcoholic Hepatitis":            {"primary":[6,18,17],   "secondary":[0,13,15]},
    "Allergy":                        {"primary":[20,3,8],    "secondary":[19,6,7]},
    "Arthritis":                      {"primary":[21,9,2],    "secondary":[12,13,0]},
    "Bronchial Asthma":               {"primary":[3,5,4],     "secondary":[11,22,2]},
    "Cervical Spondylosis":           {"primary":[1,9,14],    "secondary":[7,10,2]},
    "Chicken Pox":                    {"primary":[0,19,20],   "secondary":[2,9,12]},
    "Chronic Cholestasis":            {"primary":[20,13,2],   "secondary":[6,18,0]},
    "Common Cold":                    {"primary":[3,8,0],     "secondary":[1,12,6]},
    "Dengue":                         {"primary":[0,1,9],     "secondary":[12,2,13]},
    "Diabetes":                       {"primary":[10,23,2],   "secondary":[7,14,22]},
    "Dimorphic Hemorrhoids":          {"primary":[17,4],      "secondary":[2,13]},
    "Drug Reaction":                  {"primary":[19,20,6],   "secondary":[9,2,7]},
    "Fungal Infection":               {"primary":[20,19,9],   "secondary":[2,14]},
    "GERD":                           {"primary":[15,16,4],   "secondary":[6,3,17]},
    "Gastroenteritis":                {"primary":[6,18,17],   "secondary":[0,12,2]},
    "Heart Attack":                   {"primary":[4,5,11],    "secondary":[22,9,6]},
    "Hepatitis A":                    {"primary":[0,13,18],   "secondary":[2,12,17]},
    "Hepatitis B":                    {"primary":[0,2,23],    "secondary":[13,18,9]},
    "Hepatitis C":                    {"primary":[2,23,13],   "secondary":[0,6,18]},
    "Hepatitis D":                    {"primary":[0,6,17],    "secondary":[18,2,13]},
    "Hepatitis E":                    {"primary":[0,18,1],    "secondary":[13,2,6]},
    "Hypertension":                   {"primary":[1,10,11],   "secondary":[7,4,2]},
    "Hyperthyroidism":                {"primary":[11,14,22],  "secondary":[23,2,7]},
    "Hypoglycemia":                   {"primary":[7,11,22],   "secondary":[2,14,10]},
    "Hypothyroidism":                 {"primary":[2,14,13],   "secondary":[23,9,12]},
    "Impetigo":                       {"primary":[19,0,12],   "secondary":[20,9,2]},
    "Jaundice":                       {"primary":[20,13,17],  "secondary":[6,2,0]},
    "Malaria":                        {"primary":[0,12,22],   "secondary":[1,9,2]},
    "Migraine":                       {"primary":[1,10,6],    "secondary":[7,5,14]},
    "Osteoarthritis":                 {"primary":[21,9,14],   "secondary":[2,7,13]},
    "Paralysis Brain Hemorrhage":     {"primary":[1,7,10],    "secondary":[5,4,11]},
    "Peptic Ulcer Disease":           {"primary":[17,15,16],  "secondary":[6,13,18]},
    "Pneumonia":                      {"primary":[0,3,5],     "secondary":[4,12,22]},
    "Psoriasis":                      {"primary":[19,20,21],  "secondary":[9,2,14]},
    "Tuberculosis":                   {"primary":[3,0,23],    "secondary":[12,13,5]},
    "Typhoid":                        {"primary":[0,1,13],    "secondary":[6,17,2]},
    "Urinary Tract Infection":        {"primary":[0,17,6],    "secondary":[2,11,7]},
    "Varicose Veins":                 {"primary":[9,21,22],   "secondary":[2,13,14]},
}


def generate_row(condition, profile):
    vec = [0] * 24
    ps  = set(profile["primary"])
    ss  = set(profile["secondary"])
    for i in range(24):
        if i in ps:
            r      = random.random()
            vec[i] = 2 if r < 0.72 else (1 if r < 0.96 else 0)
        elif i in ss:
            r      = random.random()
            vec[i] = 2 if r < 0.12 else (1 if r < 0.60 else 0)
        else:
            r      = random.random()
            vec[i] = 1 if r < 0.02 else 0
    if not any(vec[i] == 2 for i in ps):
        vec[random.choice(list(ps))] = 2
    return vec + [condition]


def generate(out_path="datasets/synthetic_training_data.csv", n_samples=20000):
    os.makedirs(
        os.path.dirname(out_path) if os.path.dirname(out_path) else ".",
        exist_ok=True
    )
    rows  = []
    clist = list(CONDITIONS.keys())
    rpc   = n_samples // len(CONDITIONS)
    rem   = n_samples - rpc * len(CONDITIONS)
    for c, p in CONDITIONS.items():
        for _ in range(rpc):
            rows.append(generate_row(c, p))
    for i in range(rem):
        c = clist[i % len(clist)]
        rows.append(generate_row(c, CONDITIONS[c]))
    random.shuffle(rows)
    df   = pd.DataFrame(rows, columns=SYMPTOM_COLS + ["prognosis"])
    df.to_csv(out_path, index=False)
    dist = df["prognosis"].value_counts()
    print(f"  Generated {len(df):,} rows | "
          f"{df['prognosis'].nunique()} classes | "
          f"{dist.min()}-{dist.max()} per class")
    print(f"  Feature encoding: 0=absent  1=mild  2=severe")
    return df


if __name__ == "__main__":
    generate()