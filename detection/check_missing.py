import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")

files = list(DATA_DIR.glob("*.csv"))

missing_total = {}

for file in files:
    print(f"Checking: {file.name}")

    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()

    for column in df.columns:
        count = df[column].isna().sum()

        if count > 0:
            missing_total[column] = missing_total.get(column, 0) + count

print("\n" + "=" * 70)
print("MISSING VALUES BY FEATURE")
print("=" * 70)

if missing_total:
    for column, count in sorted(
        missing_total.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"{column}: {count}")
else:
    print("No missing values found.")