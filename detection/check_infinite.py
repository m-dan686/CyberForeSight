import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")

files = list(DATA_DIR.glob("*.csv"))

infinite_total = {}

for file in files:
    print(f"Checking: {file.name}")

    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()

    numeric = df.select_dtypes(include=np.number)

    for column in numeric.columns:
        count = np.isinf(numeric[column]).sum()

        if count > 0:
            infinite_total[column] = (
                infinite_total.get(column, 0) + count
            )

print("\n" + "=" * 70)
print("INFINITE VALUES BY FEATURE")
print("=" * 70)

if infinite_total:
    for column, count in sorted(
        infinite_total.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"{column}: {count}")
else:
    print("No infinite values found.")