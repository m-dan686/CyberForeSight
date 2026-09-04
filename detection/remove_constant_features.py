import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/cleaned")

constant_features = [
    "Bwd PSH Flags",
    "Fwd URG Flags",
    "Bwd URG Flags",
    "CWE Flag Count",
    "Fwd Avg Bytes/Bulk",
    "Fwd Avg Packets/Bulk",
    "Fwd Avg Bulk Rate",
    "Bwd Avg Bytes/Bulk",
    "Bwd Avg Packets/Bulk",
    "Bwd Avg Bulk Rate"
]

for file in DATA_DIR.glob("*.csv"):
    print(f"Processing: {file.name}")

    df = pd.read_csv(file)

    df = df.drop(columns=constant_features)

    df.to_csv(file, index=False)

    print("Columns remaining:", len(df.columns))

print("\nConstant features removed.")