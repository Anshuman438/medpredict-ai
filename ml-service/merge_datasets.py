import pandas as pd
import os

# Original 15 columns (your existing dataset format)
OLD_COLS = [
    "fever","headache","fatigue","cough","chest_pain",
    "shortness_of_breath","nausea","dizziness","sore_throat",
    "body_ache","blurred_vision","rapid_heartbeat","chills",
    "loss_of_appetite","insomnia"
]

# Full 24 columns (new format)
NEW_COLS = [
    "fever","headache","fatigue","cough","chest_pain",
    "shortness_of_breath","nausea","dizziness","sore_throat",
    "body_ache","blurred_vision","rapid_heartbeat","chills",
    "loss_of_appetite","insomnia",
    "acidity","indigestion","stomach_pain","vomiting",
    "skin_rash","itching","joint_pain","sweating","weight_loss"
]

NEW_9 = ["acidity","indigestion","stomach_pain","vomiting",
          "skin_rash","itching","joint_pain","sweating","weight_loss"]


def expand_old_dataset(path):
    """Load a 15-column CSV and expand it to 24 columns."""
    # Try with header first
    df = pd.read_csv(path, header=None)

    # Detect if last column is string (prognosis)
    last = df.iloc[:, -1]
    if last.dtype == object:
        # Has prognosis column
        if df.shape[1] == 16:
            # 15 features + prognosis (with header row)
            df.columns = OLD_COLS + ["prognosis"]
        elif df.shape[1] == 15:
            # Try reading with header
            df2 = pd.read_csv(path)
            if "prognosis" in df2.columns or "condition" in df2.columns:
                df = df2
                target = "prognosis" if "prognosis" in df.columns else "condition"
                df = df.rename(columns={target: "prognosis"})
            else:
                df.columns = OLD_COLS + ["prognosis"]
        else:
            df.columns = list(df.columns[:-1]) + ["prognosis"]
    else:
        print("WARNING: Could not detect prognosis column")
        return None

    # Add 9 new columns as 0
    for col in NEW_9:
        df[col] = 0

    # Reorder to match NEW_COLS
    df = df[NEW_COLS + ["prognosis"]]

    # Clean
    df = df[df["prognosis"].notna()]
    df = df[df["prognosis"].str.strip() != ""]
    df[NEW_COLS] = df[NEW_COLS].fillna(0).astype(int)
    df["prognosis"] = df["prognosis"].str.strip()

    print(f"  Expanded {path}: {len(df)} rows, {df['prognosis'].nunique()} classes")
    return df


def main():
    os.makedirs("datasets", exist_ok=True)

    frames = []

    # ── Load your original Training.csv ───────────────────────
    if os.path.exists("datasets/Training.csv"):
        df = expand_old_dataset("datasets/Training.csv")
        if df is not None:
            frames.append(df)
            print(f"  Loaded Training.csv: {len(df)} rows")
    else:
        print("  datasets/Training.csv not found — skipping")

    # ── Load Testing.csv if it exists ─────────────────────────
    if os.path.exists("datasets/Testing.csv"):
        df = expand_old_dataset("datasets/Testing.csv")
        if df is not None:
            frames.append(df)
            print(f"  Loaded Testing.csv: {len(df)} rows")

    # ── Load new synthetic data if it exists ──────────────────
    if os.path.exists("datasets/synthetic_training_data.csv"):
        df = pd.read_csv("datasets/synthetic_training_data.csv")
        df.columns = df.columns.str.lower().str.replace(" ", "_")
        df["prognosis"] = df["prognosis"].str.strip()
        # Make sure all 24 cols present
        for col in NEW_COLS:
            if col not in df.columns:
                df[col] = 0
        df = df[NEW_COLS + ["prognosis"]]
        frames.append(df)
        print(f"  Loaded synthetic_training_data.csv: {len(df)} rows")
    else:
        print("  No synthetic data yet — run generate_dataset.py first")

    if not frames:
        print("ERROR: No data found. Put Training.csv in datasets/ folder.")
        return

    # ── Merge all ──────────────────────────────────────────────
    merged = pd.concat(frames, ignore_index=True)
    merged = merged.drop_duplicates()
    merged = merged.sample(frac=1, random_state=42).reset_index(drop=True)

    # Save
    out = "datasets/merged_training_data.csv"
    merged.to_csv(out, index=False)

    dist = merged["prognosis"].value_counts()
    print(f"\n  Merged dataset saved -> {out}")
    print(f"  Total rows:   {len(merged)}")
    print(f"  Total classes: {merged['prognosis'].nunique()}")
    print(f"  Min per class: {dist.min()} ({dist.idxmin()})")
    print(f"  Max per class: {dist.max()} ({dist.idxmax()})")
    print(f"  Features: {len(NEW_COLS)}")
    print("\n  Class distribution:")
    for cond, count in dist.sort_index().items():
        bar = "█" * (count // 10)
        print(f"    {cond:<40} {count:>4}  {bar}")


if __name__ == "__main__":
    main()