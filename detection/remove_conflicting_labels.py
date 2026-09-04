import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/processed")
OUTPUT_DIR = Path("data/cleaned")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

all_data = []

for file in DATA_DIR.glob("*.csv"):
    df = pd.read_csv(file)
    df["source_file"] = file.name
    all_data.append(df)

combined = pd.concat(all_data, ignore_index=True)

feature_columns = [
    col for col in combined.columns
    if col not in ["Label", "source_file"]
]

# Find feature patterns that have more than one label
label_counts = (
    combined
    .groupby(feature_columns, dropna=False)["Label"]
    .nunique()
)

conflicting_groups = label_counts[label_counts > 1]

print("Conflicting groups:", len(conflicting_groups))

# Mark rows belonging to conflicting groups
conflict_index = pd.MultiIndex.from_tuples(
    conflicting_groups.index,
    names=feature_columns
)

indexed = combined.set_index(feature_columns)

conflicting_mask = indexed.index.isin(conflict_index)

cleaned = combined.loc[~conflicting_mask].copy()

print("Rows before:", len(combined))
print("Conflicting rows removed:", conflicting_mask.sum())
print("Rows after:", len(cleaned))

# Save back as separate files
for filename, group in cleaned.groupby("source_file"):
    output_file = OUTPUT_DIR / filename

    group = group.drop(columns=["source_file"])

    group.to_csv(output_file, index=False)

print("\nCleaned dataset created successfully!")