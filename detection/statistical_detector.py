import pandas as pd

df = pd.read_csv("data/device_telemetry.csv")

# Create a controlled abnormal event
df.loc[70, "packets_received_per_sec"] = 1000

mean = df["packets_received_per_sec"].mean()
std = df["packets_received_per_sec"].std()

df["z_score"] = (
    (df["packets_received_per_sec"] - mean) / std
)

df["anomaly"] = df["z_score"].abs() > 3

print(df.loc[70, [
    "timestamp",
    "packets_received_per_sec",
    "z_score",
    "anomaly"
]])