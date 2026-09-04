import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/cleaned")

file = next(DATA_DIR.glob("*.csv"))
df = pd.read_csv(file)

features = [
    "Fwd Packet Length Max",
    "Fwd Packet Length Mean",
    "Destination Port",
    "Init_Win_bytes_forward",
    "act_data_pkt_fwd",
    "Total Length of Fwd Packets",
    "Fwd Header Length",
    "Fwd Packet Length Std",
    "Fwd IAT Std",
    "Bwd Packet Length Min",
    "Total Fwd Packets",
    "Fwd IAT Max",
    "Fwd IAT Mean",
    "Bwd Header Length",
    "Bwd Packet Length Max",
    "Bwd Packet Length Mean",
    "Fwd IAT Total",
    "Init_Win_bytes_backward",
    "Packet Length Mean",
    "Total Backward Packets"
]

print("Selected features:", len(features))

for feature in features:
    print(feature)