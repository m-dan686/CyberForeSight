import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("data/raw/cic-ids2017")

files = list(DATA_DIR.glob("*.csv"))

for file in files:
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()

    invalid = (
        df["Flow Bytes/s"].isna()
        | np.isinf(df["Flow Bytes/s"])
        | np.isinf(df["Flow Packets/s"])
    )

    if invalid.sum() > 0:
        print("\n" + "=" * 70)
        print(file.name)
        print("Invalid rows:", invalid.sum())

        print(
            df.loc[
                invalid,
                [
                    "Flow Duration",
                    "Total Fwd Packets",
                    "Total Backward Packets",
                    "Total Length of Fwd Packets",
                    "Total Length of Bwd Packets",
                    "Flow Bytes/s",
                    "Flow Packets/s",
                    "Label"
                ]
            ].head(10).to_string(index=False)
        )