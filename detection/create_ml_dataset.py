import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/cleaned")
OUTPUT_DIR = Path("data/ml")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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

columns = features + ["Label"]

for file in DATA_DIR.glob("*.csv"):
    df = pd.read_csv(file)

    ml_df = df[columns]

    output_file = OUTPUT_DIR / file.name
    ml_df.to_csv(output_file, index=False)

    print(file.name, "→", len(ml_df), "rows,", len(ml_df.columns), "columns")

print("\nML datasets created.")