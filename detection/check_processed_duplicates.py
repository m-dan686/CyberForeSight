import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/processed")

for file in DATA_DIR.glob("*.csv"):

    df = pd.read_csv(file)

    print("\n" + "=" * 60)
    print(file.name)
    print("Rows:", len(df))
    print("Duplicate rows:", df.duplicated().sum())
    print("Missing values:", df.isna().sum().sum())