import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")

files = list(DATA_DIR.glob("*.csv"))

all_data = []

for file in files:
    print(f"Reading: {file.name}")

    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()

    # Add source file information
    df["source_file"] = file.name

    all_data.append(df)

combined = pd.concat(all_data, ignore_index=True)

# Find rows duplicated across the complete dataset
duplicate_mask = combined.duplicated(
    subset=combined.columns.drop("source_file"),
    keep=False
)

duplicates = combined[duplicate_mask]

# Count how many different files contain each duplicated row
group_columns = list(combined.columns.drop("source_file"))

cross_file = (
    duplicates.groupby(group_columns, dropna=False)["source_file"]
    .nunique()
)

cross_file_duplicates = cross_file[cross_file > 1]

print("\n" + "=" * 70)
print("CROSS-FILE DUPLICATE ANALYSIS")
print("=" * 70)

print("Duplicate rows appearing in multiple files:",
      len(cross_file_duplicates))

print("\nNumber of files containing those duplicated rows:")

print(cross_file_duplicates.value_counts().sort_index())