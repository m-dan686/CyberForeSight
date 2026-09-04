import pandas as pd
from pathlib import Path
from itertools import combinations
from collections import Counter

DATA_DIR = Path("data/raw/cic-ids2017")

all_data = []

for file in DATA_DIR.glob("*.csv"):
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    all_data.append(df)

combined = pd.concat(all_data, ignore_index=True)

feature_columns = [
    col for col in combined.columns
    if col != "Label"
]

# Find feature groups having multiple labels
grouped = combined.groupby(
    feature_columns,
    dropna=False
)["Label"].unique()

conflicting = grouped[grouped.apply(len) > 1]

pairs = Counter()

for labels in conflicting:
    labels = sorted(str(label) for label in labels)

    for pair in combinations(labels, 2):
        pairs[pair] += 1

print("\n" + "=" * 70)
print("CONFLICTING LABEL PAIRS")
print("=" * 70)

print("Total conflicting groups:", len(conflicting))

for pair, count in pairs.most_common():
    print(f"{pair[0]}  <-->  {pair[1]} : {count}")
