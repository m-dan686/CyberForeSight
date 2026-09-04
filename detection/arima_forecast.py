import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

df = pd.read_csv("data/ml/cic_ml_dataset.csv")

df["attack"] = (df["Label"] != "BENIGN").astype(int)
df["batch"] = df.index // 1000

attack_counts = df.groupby("batch")["attack"].sum()

model = ARIMA(attack_counts, order=(1, 1, 1))
model_fit = model.fit()

forecast = model_fit.forecast(steps=5)

print("Latest attack count:", attack_counts.iloc[-1])
print("\nNext 5 forecasts:")

for i, value in enumerate(forecast, 1):
    print(f"Batch {i}: {value:.2f}")