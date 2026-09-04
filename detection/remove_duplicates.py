import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/processed")

for file in DATA_DIR.glob("*.csv"):

    print(f"Processing: {file.name}")

    df = pd.read_csv(file)

    before = len(df)

    # Remove exact duplicate rows
    df = df.drop_duplicates()

    after = len(df)

    print("Rows before:", before)
    print("Rows after :", after)
    print("Removed    :", before - after)

    df.to_csv(file, index=False)

print("\nDuplicate removal completed.")