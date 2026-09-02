import pandas as pd

# Load our telemetry
df = pd.read_csv("data/device_telemetry.csv")

# Select normal telemetry features
baseline = df[
    [
        "timestamp",
        "cpu_percent",
        "memory_percent",
        "bytes_sent_per_sec",
        "bytes_received_per_sec",
        "packets_sent_per_sec",
        "packets_received_per_sec"
    ]
]

# Save baseline
baseline.to_csv("data/normal_baseline.csv", index=False)

print("Baseline created successfully!")
print("Rows:", len(baseline))