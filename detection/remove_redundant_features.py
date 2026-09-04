import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/cleaned")

remove = [
    "Fwd PSH Flags",
    "ECE Flag Count"
]

for file in DATA_DIR.glob("*.csv"):
    df = pd.read_csv(file)

    df = df.drop(columns=remove)

    df.to_csv(file, index=False)

    print(file.name, "→", len(df.columns), "columns")

print("Done.")