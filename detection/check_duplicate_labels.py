import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")

all_data = []

for file in DATA_DIR.glob("*.csv"):
    print(f"Reading: {file.name}")

    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()

    all_data.append(df)

combined = pd.concat(all_data, ignore_index=True)

feature_columns = [
    col for col in combined.columns
    if col != "Label"
]

# Keep only rows that occur across multiple files
duplicate_mask = combined.duplicated(
    subset=feature_columns,
    keep=False
)

duplicates = combined[duplicate_mask]

# For each identical feature set, count different labels
label_counts = (
    duplicates
    .groupby(feature_columns, dropna=False)["Label"]
    .nunique()
)

conflicting = label_counts[label_counts > 1]

same_label = label_counts[label_counts == 1]

print("\n" + "=" * 70)
print("DUPLICATE LABEL ANALYSIS")
print("=" * 70)

print("Duplicate feature groups:", len(label_counts))
print("Same-label duplicate groups:", len(same_label))
print("Conflicting-label groups:", len(conflicting))

if len(conflicting) > 0:
    print("\n⚠️ Conflicting labels found!")
else:
    print("\n✅ No conflicting labels found.")