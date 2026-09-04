import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/processed")

for file in DATA_DIR.glob("*.csv"):
    df = pd.read_csv(file)

    missing = df.isna().sum()
    missing = missing[missing > 0]

    print("\n" + "=" * 60)
    print(file.name)

    if missing.empty:
        print("No missing values")
    else:
        print(missing)