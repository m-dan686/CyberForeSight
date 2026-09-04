import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")
OUTPUT_DIR = Path("data/processed")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for file in DATA_DIR.glob("*.csv"):

    print(f"Processing: {file.name}")

    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()

    # Convert infinite values to NaN
    df = df.replace([float("inf"), float("-inf")], pd.NA)

    # Zero-duration flows produce undefined rates.
    # Represent those rates as 0 in the processed dataset.
    df["Flow Bytes/s"] = df["Flow Bytes/s"].fillna(0)
    df["Flow Packets/s"] = df["Flow Packets/s"].fillna(0)

    output_file = OUTPUT_DIR / file.name

    df.to_csv(output_file, index=False)

    print(f"Saved: {output_file}")