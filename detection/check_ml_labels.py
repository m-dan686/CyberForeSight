import pandas as pd

df = pd.read_csv("data/ml/cic_ml_dataset.csv")

print(df["Label"].value_counts())