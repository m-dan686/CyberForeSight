import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/cleaned")

file = next(DATA_DIR.glob("*.csv"))
df = pd.read_csv(file)

features = df.drop(columns=["Label"])

constant = features.nunique()

constant = constant[constant <= 1]

print("Constant features:", len(constant))

for column in constant.index:
    print(column)