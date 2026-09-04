import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/ml")
OUTPUT = DATA_DIR / "cic_ml_dataset.csv"

files = list(DATA_DIR.glob("*.csv"))

# Don't include the combined file itself
files = [f for f in files if f.name != OUTPUT.name]

dfs = [pd.read_csv(file) for file in files]

combined = pd.concat(dfs, ignore_index=True)

combined.to_csv(OUTPUT, index=False)

print("Rows:", len(combined))
print("Columns:", len(combined.columns))
print("Saved:", OUTPUT)