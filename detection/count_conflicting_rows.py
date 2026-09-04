import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/processed")

all_data = []

for file in DATA_DIR.glob("*.csv"):
    df = pd.read_csv(file)
    all_data.append(df)

combined = pd.concat(all_data, ignore_index=True)

feature_columns = [
    col for col in combined.columns
    if col != "Label"
]

grouped = combined.groupby(
    feature_columns,
    dropna=False
)["Label"].nunique()

conflicting_groups = grouped[grouped > 1]

print("Conflicting feature groups:", len(conflicting_groups))

# Find all rows belonging to conflicting groups
conflict_index = pd.MultiIndex.from_tuples(
    conflicting_groups.index,
    names=feature_columns
)

indexed = combined.set_index(feature_columns)

conflicting_rows = indexed[
    indexed.index.isin(conflict_index)
].reset_index()

print("Actual rows affected:", len(conflicting_rows))

print("\nLabels among affected rows:")
print(conflicting_rows["Label"].value_counts())