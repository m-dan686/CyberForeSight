import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/cleaned")

file = next(DATA_DIR.glob("*.csv"))

df = pd.read_csv(file)

print("Columns:", len(df.columns))

for i, column in enumerate(df.columns, start=1):
    print(f"{i}. {column}")