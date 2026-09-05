"""Flow-level extraction: CIC-IDS flow CSV -> canonical schema.

Reads any CIC-IDS 2017/2018 (or CSE-CIC-IDS 2018) 'MachineLearningCSV'
flow CSV, maps its columns onto the canonical schema defined in schema.py,
cleans infinities / constant columns / duplicate headers, and it canonicalizes
the 'Label' column into binary + attack-class columns.  Output is a single
tidy flows table saved to the processed data directory.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .schema import CANONICAL_FEATURES, FLOW_ALIAS, canonical_label

_COMMON_DT_FORMATS = ("%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S")


def resolve_columns(source_columns: Iterable[str]) -> dict[str, str]:
    """Map canonical names -> actual source CSV columns, raising on missing required."""
    lower_to_actual = {str(c).strip().lower(): c for c in source_columns}
    mapping: dict[str, str] = {}
    for canon, aliases in FLOW_ALIAS.items():
        for alias in aliases:
            key = alias.lower()
            if key in lower_to_actual:
                mapping[canon] = lower_to_actual[key]
                break
    required = {"dst_port", "protocol", "timestamp", "label"}
    missing = required - set(mapping)
    if missing:
        raise ValueError(f"missing required CIC columns {sorted(missing)}")
    return mapping


def infer_timestamp_format(series: pd.Series) -> str:
    """Pick a datetime parse format that actually works on the given column."""
    sample = series.dropna().head(50).astype(str)
    if sample.empty:
        return "%d/%m/%Y %H:%M:%S"
    for fmt in _COMMON_DT_FORMATS:
        ok = 0
        for v in sample:
            try:
                pd.to_datetime(v, format=fmt)
                ok += 1
            except (ValueError, TypeError):
                break
        if ok == len(sample):
            return fmt
    return _COMMON_DT_FORMATS[0]


def extract_flow_csv(
    csv_path: str | Path,
    source_name: str | None = None,
    drop_constant: bool = True,
) -> pd.DataFrame:
    """Load a CIC-IDS flow CSV and return the canonical flows dataframe."""
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path, low_memory=False)
    df = df.dropna(how="all")

    mapping = resolve_columns(df.columns)
    df = df[list(mapping.values())].rename(columns={v: k for k, v in mapping.items()})

    keep = [c for c in CANONICAL_FEATURES if c in df.columns]
    df = df[keep]

    df["label"] = df["label"].map(canonical_label)
    df["attack"] = (df["label"] != "Benign").astype(np.int8)

    for col in df.columns:
        if col in ("label", "timestamp"):
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if drop_constant:
        const_cols = [c for c in df.columns if c not in ("timestamp", "label") and df[c].nunique(dropna=True) <= 1]
        if const_cols:
            df = df.drop(columns=const_cols)
            print(f"  dropped constant columns: {const_cols}", file=sys.stderr)

    ts_fmt = infer_timestamp_format(df["timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], format=ts_fmt, errors="coerce")
    dropped_missing = df["timestamp"].isna().sum()
    df = df.dropna(subset=["timestamp"])
    if dropped_missing:
        print(f"  dropped {dropped_missing} rows with unparseable timestamps", file=sys.stderr)

    df["flow_duration"] = pd.to_numeric(df.get("flow_duration"), errors="coerce").fillna(0.0)
    df.fillna(0.0, inplace=True)
    df = df.replace([np.inf, -np.inf], 0.0)
    df = df.sort_values("timestamp").reset_index(drop=True)

    if source_name is None:
        source_name = csv_path.stem
    df.attrs["source"] = source_name
    return df


def build_flows_ml_datasets(
    flows: pd.DataFrame,
    ml_dir: str | Path,
    binary_features: list[str] | None = None,
) -> dict[str, Path]:
    """Write the name-labelled and binary flow rows used by ML stages."""
    ml_dir = Path(ml_dir)
    ml_dir.mkdir(parents=True, exist_ok=True)

    if binary_features is None:
        binary_features = [
            "dst_port",
            "protocol",
            "flow_duration",
            "tot_fwd_pkts",
            "tot_bwd_pkts",
            "tot_fwd_byts",
            "tot_bwd_byts",
            "fwd_iat_mean",
            "bwd_iat_mean",
            "syn_cnt",
            "ack_cnt",
            "fin_cnt",
            "rst_cnt",
            "down_up_ratio",
            "init_fwd_win",
            "init_bwd_win",
        ]

    ml_out = ml_dir / "cic_ml_dataset.csv"
    flows_out = flows[["timestamp", "label"] + binary_features].copy()
    flows_out["timestamp"] = flows_out["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    flows_out.to_csv(ml_out, index=False)

    bin_out = ml_dir / "cic_binary_dataset.csv"
    binary = flows[["timestamp", "label", "attack"] + binary_features].copy()
    binary["timestamp"] = binary["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    binary.to_csv(bin_out, index=False)

    return {"ml": ml_out, "binary": bin_out}