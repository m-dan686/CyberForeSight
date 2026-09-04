import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")

files = list(DATA_DIR.glob("*.csv"))

print("Files found:", len(files))
print()

for file in files:
    print("=" * 70)
    print("FILE:", file.name)

    df = pd.read_csv(file)

    print("Rows:", len(df))
    print("Columns:", len(df.columns))

    print("\nLabels:")
    print(df[" Label"].value_counts() if " Label" in df.columns else df["Label"].value_counts())

    print("\nMissing values:", df.isnull().sum().sum())
    print("Duplicate rows:", df.duplicated().sum())

    print()