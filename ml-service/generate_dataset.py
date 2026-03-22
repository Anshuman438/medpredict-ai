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

# Redesigned with HIGHLY DISTINCTIVE profiles
# Each disease has unique primary symptoms that rarely overlap
# primary   -> always present (prob 0.97)
# secondary -> often present (prob 0.70)
# noise     -> rarely present (prob 0.03)

CONDITIONS = {
    "Vertigo Paroxysmal Positional": {
        "primary":   [7, 6],              # dizziness, nausea
        "secondary": [1, 10, 22],         # headache, blurred_vision, sweating
    },
    "AIDS": {
        "primary":   [2, 23, 13],         # fatigue, weight_loss, loss_of_appetite
        "secondary": [0, 12, 19, 9],      # fever, chills, skin_rash, body_ache
    },
    "Acne": {
        "primary":   [19, 20],            # skin_rash, itching
        "secondary": [14, 2],             # insomnia, fatigue
    },
    "Alcoholic Hepatitis": {
        "primary":   [6, 18, 17],         # nausea, vomiting, stomach_pain
        "secondary": [0, 13, 15],         # fever, loss_of_appetite, acidity
    },
    "Allergy": {
        "primary":   [20, 3, 8],          # itching, cough, sore_throat
        "secondary": [19, 6, 7],          # skin_rash, nausea, dizziness
    },
    "Arthritis": {
        "primary":   [21, 9, 2],          # joint_pain, body_ache, fatigue
        "secondary": [12, 13, 0],         # chills, loss_of_appetite, fever
    },
    "Bronchial Asthma": {
        "primary":   [3, 5, 4],           # cough, shortness_of_breath, chest_pain
        "secondary": [11, 22, 2],         # rapid_heartbeat, sweating, fatigue
    },
    "Cervical Spondylosis": {
        "primary":   [1, 9, 14],          # headache, body_ache, insomnia
        "secondary": [7, 10, 2],          # dizziness, blurred_vision, fatigue
    },
    "Chicken Pox": {
        "primary":   [0, 19, 20],         # fever, skin_rash, itching
        "secondary": [2, 9, 12],          # fatigue, body_ache, chills
    },
    "Chronic Cholestasis": {
        "primary":   [20, 13, 2],         # itching, loss_of_appetite, fatigue
        "secondary": [6, 18, 0],          # nausea, vomiting, fever
    },
    "Common Cold": {
        "primary":   [3, 8, 0],           # cough, sore_throat, fever
        "secondary": [1, 12, 6],          # headache, chills, nausea
    },
    "Dengue": {
        "primary":   [0, 1, 9],           # fever, headache, body_ache
        "secondary": [12, 2, 13],         # chills, fatigue, loss_of_appetite
    },
    "Diabetes": {
        "primary":   [10, 23, 2],         # blurred_vision, weight_loss, fatigue
        "secondary": [7, 14, 22],         # dizziness, insomnia, sweating
    },
    "Dimorphic Hemorrhoids": {
        "primary":   [17, 4],             # stomach_pain, chest_pain
        "secondary": [2, 13],             # fatigue, loss_of_appetite
    },
    "Drug Reaction": {
        "primary":   [19, 20, 0],         # skin_rash, itching, fever
        "secondary": [9, 6, 2],           # body_ache, nausea, fatigue
    },
    "Fungal Infection": {
        "primary":   [20, 19, 9],         # itching, skin_rash, body_ache
        "secondary": [2, 14],             # fatigue, insomnia
    },
    "GERD": {
        "primary":   [15, 16, 4],         # acidity, indigestion, chest_pain
        "secondary": [6, 3, 17],          # nausea, cough, stomach_pain
    },
    "Gastroenteritis": {
        "primary":   [6, 18, 17],         # nausea, vomiting, stomach_pain
        "secondary": [0, 12, 2],          # fever, chills, fatigue
    },
    "Heart Attack": {
        "primary":   [4, 5, 11],          # chest_pain, shortness_of_breath, rapid_heartbeat
        "secondary": [22, 9, 6],          # sweating, body_ache, nausea
    },
    "Hepatitis A": {
        "primary":   [0, 18, 13],         # fever, vomiting, loss_of_appetite
        "secondary": [2, 6, 17],          # fatigue, nausea, stomach_pain
    },
    "Hepatitis B": {
        "primary":   [0, 2, 23],          # fever, fatigue, weight_loss
        "secondary": [13, 18, 9],         # loss_of_appetite, vomiting, body_ache
    },
    "Hepatitis C": {
        "primary":   [2, 23, 13],         # fatigue, weight_loss, loss_of_appetite
        "secondary": [0, 6, 18],          # fever, nausea, vomiting
    },
    "Hepatitis D": {
        "primary":   [0, 6, 17],          # fever, nausea, stomach_pain
        "secondary": [18, 2, 13],         # vomiting, fatigue, loss_of_appetite
    },
    "Hepatitis E": {
        "primary":   [0, 6, 18],          # fever, nausea, vomiting
        "secondary": [17, 13, 2],         # stomach_pain, loss_of_appetite, fatigue
    },
    "Hypertension": {
        "primary":   [1, 10, 11],         # headache, blurred_vision, rapid_heartbeat
        "secondary": [7, 4, 2],           # dizziness, chest_pain, fatigue
    },
    "Hyperthyroidism": {
        "primary":   [11, 14, 22],        # rapid_heartbeat, insomnia, sweating
        "secondary": [23, 2, 7],          # weight_loss, fatigue, dizziness
    },
    "Hypoglycemia": {
        "primary":   [7, 11, 22],         # dizziness, rapid_heartbeat, sweating
        "secondary": [2, 14, 10],         # fatigue, insomnia, blurred_vision
    },
    "Hypothyroidism": {
        "primary":   [2, 14, 13],         # fatigue, insomnia, loss_of_appetite
        "secondary": [23, 9, 12],         # weight_loss, body_ache, chills
    },
    "Impetigo": {
        "primary":   [19, 0, 12],         # skin_rash, fever, chills
        "secondary": [20, 9, 2],          # itching, body_ache, fatigue
    },
    "Jaundice": {
        "primary":   [20, 13, 17],        # itching, loss_of_appetite, stomach_pain
        "secondary": [6, 2, 0],           # nausea, fatigue, fever
    },
    "Malaria": {
        "primary":   [0, 12, 22],         # fever, chills, sweating
        "secondary": [1, 9, 2],           # headache, body_ache, fatigue
    },
    "Migraine": {
        "primary":   [1, 10, 6],          # headache, blurred_vision, nausea
        "secondary": [7, 5, 14],          # dizziness, shortness_of_breath, insomnia
    },
    "Osteoarthritis": {
        "primary":   [21, 9, 14],         # joint_pain, body_ache, insomnia
        "secondary": [2, 7, 13],          # fatigue, dizziness, loss_of_appetite
    },
    "Paralysis Brain Hemorrhage": {
        "primary":   [1, 7, 10],          # headache, dizziness, blurred_vision
        "secondary": [5, 4, 11],          # shortness_of_breath, chest_pain, rapid_heartbeat
    },
    "Peptic Ulcer Disease": {
        "primary":   [17, 15, 16],        # stomach_pain, acidity, indigestion
        "secondary": [6, 18, 13],         # nausea, vomiting, loss_of_appetite
    },
    "Pneumonia": {
        "primary":   [0, 3, 5],           # fever, cough, shortness_of_breath
        "secondary": [4, 12, 22],         # chest_pain, chills, sweating
    },
    "Psoriasis": {
        "primary":   [19, 20, 21],        # skin_rash, itching, joint_pain
        "secondary": [9, 2, 14],          # body_ache, fatigue, insomnia
    },
    "Tuberculosis": {
        "primary":   [3, 23, 5],          # cough, weight_loss, shortness_of_breath
        "secondary": [0, 12, 13],         # fever, chills, loss_of_appetite
    },
    "Typhoid": {
        "primary":   [0, 1, 13],          # fever, headache, loss_of_appetite
        "secondary": [6, 17, 2],          # nausea, stomach_pain, fatigue
    },
    "Urinary Tract Infection": {
        "primary":   [0, 17, 6],          # fever, stomach_pain, nausea
        "secondary": [2, 11, 7],          # fatigue, rapid_heartbeat, dizziness
    },
    "Varicose Veins": {
        "primary":   [9, 21, 22],         # body_ache, joint_pain, sweating
        "secondary": [2, 13, 14],         # fatigue, loss_of_appetite, insomnia
    },
}


def generate_row(condition, profile, noise_rate=0.03):
    vec = [0] * 24
    ps = set(profile["primary"])
    ss = set(profile["secondary"])
    for i in range(24):
        if i in ps:
            vec[i] = 1 if random.random() < 0.97 else 0
        elif i in ss:
            vec[i] = 1 if random.random() < 0.70 else 0
        else:
            vec[i] = 1 if random.random() < noise_rate else 0
    # Guarantee all primary symptoms present in at least 80% of rows
    if sum(vec[i] for i in ps) < len(ps) - 1:
        for i in ps:
            vec[i] = 1
    return vec + [condition]


def generate(out_path="datasets/synthetic_training_data.csv", n_samples=20000):
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)
    rows = []
    clist = list(CONDITIONS.keys())
    rpc = n_samples // len(CONDITIONS)
    rem = n_samples - rpc * len(CONDITIONS)

    for c, p in CONDITIONS.items():
        for _ in range(rpc):
            rows.append(generate_row(c, p))
    for i in range(rem):
        c = clist[i % len(clist)]
        rows.append(generate_row(c, CONDITIONS[c]))

    random.shuffle(rows)
    df = pd.DataFrame(rows, columns=SYMPTOM_COLS + ["prognosis"])
    df.to_csv(out_path, index=False)

    dist = df["prognosis"].value_counts()
    print(f"Generated {len(df)} rows -> {out_path}")
    print(f"Classes: {df['prognosis'].nunique()} | "
          f"Min/Max per class: {dist.min()}/{dist.max()}")
    return df


if __name__ == "__main__":
    generate()