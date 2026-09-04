import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/cleaned")

file = next(DATA_DIR.glob("*.csv"))
df = pd.read_csv(file)

features = df.drop(columns=["Label"])

corr = features.corr().abs()

pairs = []

for i in range(len(corr.columns)):
    for j in range(i + 1, len(corr.columns)):
        value = corr.iloc[i, j]

        if value >= 0.95:
            pairs.append((
                corr.columns[i],
                corr.columns[j],
                value
            ))

print("Highly correlated pairs:", len(pairs))

for a, b, value in sorted(pairs, key=lambda x: x[2], reverse=True):
    print(f"{a} <-> {b}: {value:.4f}")