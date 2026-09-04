import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")

files = list(DATA_DIR.glob("*.csv"))

total_duplicates = 0
duplicate_labels = {}

for file in files:
    print(f"Checking: {file.name}")

    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()

    duplicate_mask = df.duplicated(keep=False)

    duplicates = df[duplicate_mask].copy()

    total_duplicates += df.duplicated().sum()

    if not duplicates.empty:
        counts = duplicates["Label"].astype(str).str.strip().value_counts()

        for label, count in counts.items():
            duplicate_labels[label] = (
                duplicate_labels.get(label, 0) + count
            )

print("\n" + "=" * 70)
print("DUPLICATE ANALYSIS")
print("=" * 70)

print("Total duplicate rows:", f"{total_duplicates:,}")

print("\nDuplicate rows by label:")

for label, count in sorted(
    duplicate_labels.items(),
    key=lambda x: x[1],
    reverse=True
):
    print(f"{label}: {count:,}")