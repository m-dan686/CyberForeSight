import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")

files = list(DATA_DIR.glob("*.csv"))

missing = 0
infinite = 0

for file in files:
    print(f"Checking: {file.name}")

    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()

    missing += df["Flow Bytes/s"].isna().sum()

    numeric = df.select_dtypes(include=np.number)

    infinite += np.isinf(numeric).sum().sum()

print("\n" + "=" * 70)
print("INVALID VALUE SUMMARY")
print("=" * 70)

print("Missing Flow Bytes/s:", missing)
print("Infinite numeric values:", infinite)