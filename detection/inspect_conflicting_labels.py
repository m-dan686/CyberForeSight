import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")

all_data = []

for file in DATA_DIR.glob("*.csv"):
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    df["source_file"] = file.name
    all_data.append(df)

combined = pd.concat(all_data, ignore_index=True)

feature_columns = [
    col for col in combined.columns
    if col not in ["Label", "source_file"]
]

duplicate_mask = combined.duplicated(
    subset=feature_columns,
    keep=False
)

duplicates = combined[duplicate_mask]

label_counts = (
    duplicates
    .groupby(feature_columns, dropna=False)["Label"]
    .nunique()
)

conflicting_groups = label_counts[label_counts > 1]

print("Conflicting groups:", len(conflicting_groups))

print("\nFirst 5 conflicting groups:\n")

for i, feature_values in enumerate(conflicting_groups.index[:5], start=1):

    mask = (duplicates[feature_columns] == feature_values).all(axis=1)

    result = duplicates.loc[
        mask,
        ["Label", "source_file"]
    ].drop_duplicates()

    print(f"\n--- Group {i} ---")
    print(result.to_string(index=False))