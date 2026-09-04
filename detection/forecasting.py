import pandas as pd

df = pd.read_csv("data/ml/cic_ml_dataset.csv")

df["attack"] = (df["Label"] != "BENIGN").astype(int)

# Create batches of 1000 flows
df["batch"] = df.index // 1000

attack_counts = df.groupby("batch")["attack"].sum()

# EWMA
forecast = attack_counts.ewm(span=10).mean()

print("Latest attack count:", attack_counts.iloc[-1])
print("Forecast:", round(forecast.iloc[-1], 2))