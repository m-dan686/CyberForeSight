import pandas as pd

INPUT = "data/ml/cic_ml_dataset.csv"
OUTPUT = "data/ml/cic_binary_dataset.csv"

df = pd.read_csv(INPUT)

df["Label"] = (df["Label"] != "BENIGN").astype(int)

df.to_csv(OUTPUT, index=False)

print(df["Label"].value_counts())
print("Saved:", OUTPUT)