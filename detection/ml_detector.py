import pandas as pd
from sklearn.ensemble import IsolationForest

# Load normal baseline
df = pd.read_csv("data/normal_baseline.csv")

# Select features
features = [
    "cpu_percent",
    "memory_percent",
    "bytes_sent_per_sec",
    "bytes_received_per_sec",
    "packets_sent_per_sec",
    "packets_received_per_sec"
]

X = df[features]

# Create Isolation Forest model
model = IsolationForest(
    contamination=0.05,
    random_state=42
)

# Train model and predict
df["prediction"] = model.fit_predict(X)

# Convert result to readable form
df["anomaly"] = df["prediction"] == -1

print(df[[
    "timestamp",
    "packets_received_per_sec",
    "prediction",
    "anomaly"
]].tail(10))