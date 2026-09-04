import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")

files = list(DATA_DIR.glob("*.csv"))

all_labels = []
total_rows = 0
total_duplicates = 0
total_missing = 0

for file in files:
    print(f"Reading: {file.name}")

    df = pd.read_csv(file)

    # Remove only whitespace from column names in memory
    df.columns = df.columns.str.strip()

    total_rows += len(df)
    total_duplicates += df.duplicated().sum()
    total_missing += df.isnull().sum().sum()

    all_labels.extend(df["Label"].astype(str).str.strip())

print("\n" + "=" * 70)
print("CIC-IDS2017 DATASET SUMMARY")
print("=" * 70)

print("\nTotal files:", len(files))
print("Total rows:", f"{total_rows:,}")
print("Total duplicate rows:", f"{total_duplicates:,}")
print("Total missing values:", f"{total_missing:,}")

print("\nLabel distribution:")
label_counts = pd.Series(all_labels).value_counts()

print(label_counts.to_string())

print("\nTotal classes:", len(label_counts))