"""Windowing: aggregate canonical flows into fixed-length network-state vectors S_t.

Each time window (default 60 s) becomes one feature vector combining flow
aggregates, TCP flag pressure, inter-arrival timing, and bidi ratios, plus a
ground-truth label.  A robust scaler is fit on benign windows only (so attack
signals are never masked by benign scale) and persisted to json for reuse at
forecast/inference time.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .schema import STATE_FEATURES

_AGG: dict[str, list[str]] = {
    "flow_count": ["attack", "size"],
    "dst_port_uniq": ["dst_port", "nunique"],
    "protocol_uniq": ["protocol", "nunique"],
    "fwd_pkts": ["tot_fwd_pkts", "sum"],
    "bwd_pkts": ["tot_bwd_pkts", "sum"],
    "fwd_byts": ["tot_fwd_byts", "sum"],
    "bwd_byts": ["tot_bwd_byts", "sum"],
    "flow_duration_mean": ["flow_duration", "mean"],
    "flow_duration_sum": ["flow_duration", "sum"],
    "flow_byts_p_s_mean": ["flow_byts_p_s", "mean"],
    "flow_pkts_p_s_mean": ["flow_pkts_p_s", "mean"],
    "flow_iat_mean": ["flow_iat_mean", "mean"],
    "flow_iat_std": ["flow_iat_std", "mean"],
    "flow_iat_max": ["flow_iat_max", "max"],
    "fwd_iat_mean": ["fwd_iat_mean", "mean"],
    "fwd_iat_std": ["fwd_iat_std", "mean"],
    "fwd_iat_max": ["fwd_iat_max", "max"],
    "bwd_iat_mean": ["bwd_iat_mean", "mean"],
    "bwd_iat_std": ["bwd_iat_std", "mean"],
    "bwd_iat_max": ["bwd_iat_max", "max"],
    "pkt_len_mean": ["pkt_len_mean", "mean"],
    "pkt_len_std": ["pkt_len_std", "mean"],
    "syn_cnt": ["syn_cnt", "sum"],
    "ack_cnt": ["ack_cnt", "sum"],
    "fin_cnt": ["fin_cnt", "sum"],
    "rst_cnt": ["rst_cnt", "sum"],
    "psh_cnt": ["psh_cnt", "sum"],
    "urg_cnt": ["urg_cnt", "sum"],
    "down_up_ratio": ["down_up_ratio", "mean"],
    "init_fwd_win": ["init_fwd_win", "mean"],
    "init_bwd_win": ["init_bwd_win", "mean"],
    "fwd_act_data_pkts": ["fwd_act_data_pkts", "sum"],
    "fwd_seg_size_min": ["fwd_seg_size_min", "mean"],
    "subflow_fwd_pkts": ["subflow_fwd_pkts", "sum"],
    "subflow_bwd_pkts": ["subflow_bwd_pkts", "sum"],
    "attack_flows": ["attack", "sum"],
}

# Aggregates required by the state vector that _AGG references conditionally.
_OPTIONAL = {
    "down_up_ratio",
    "init_fwd_win",
    "init_bwd_win",
    "fwd_act_data_pkts",
    "fwd_seg_size_min",
    "subflow_fwd_pkts",
    "subflow_bwd_pkts",
}


def build_windows(
    flows: pd.DataFrame,
    window_seconds: int = 60,
    scaler_path: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Build windowed state vectors S_t with a benign-fit robust scaler."""
    flows = flows.copy()
    if "attack" not in flows.columns:
        flows["attack"] = (flows["label"] != "Benign").astype(np.int8)

    if not flows["timestamp"].is_monotonic_increasing:
        flows = flows.sort_values("timestamp")

    edges = pd.to_datetime(flows["timestamp"])
    groups = flows.groupby(edges.dt.floor(f"{window_seconds}s"), sort=True)

    agg_spec: dict[str, list[str]] = {}
    for out_col, value in _AGG.items():
        src, how = value
        if src not in flows.columns and src not in ("dst_port", "protocol", "attack", "flow_count"):
            src = src
        if src not in flows.columns:
            continue
        agg_spec[out_col] = pd.NamedAgg(column=src, aggfunc=how)

    windows = groups.agg(**agg_spec).reset_index()
    windows = windows.rename(columns={windows.columns[0]: "window_start"})

    windows["flow_count"] = windows["flow_count"].fillna(0).astype(float)
    windows["pkt_bytes_ratio"] = np.where(
        windows["bwd_byts"] > 0, windows["fwd_byts"] / windows["bwd_byts"], 0.0
    )
    windows["pkt_count_ratio"] = np.where(
        windows["bwd_pkts"] > 0, windows["fwd_pkts"] / windows["bwd_pkts"], 0.0
    )
    windows["attack_frac"] = windows["attack_flows"] / windows["flow_count"].clip(lower=1.0)
    windows["attack"] = (windows["attack_frac"] > 0).astype(np.int8)
    windows["label"] = groups["label"].first().reset_index(drop=True)

    present = [c for c in STATE_FEATURES if c in windows.columns]
    raw = windows[present].copy()

    scaler = _fit_robust_scaler(raw, windows["attack"] == 0)
    normed = (raw - scaler["median"]) / np.clip(scaler["iqr"], 1e-9, None)
    normed = normed.clip(lower=-5.0, upper=5.0).fillna(0.0)
    normed.columns = [f"state_{c}" for c in present]

    out = pd.concat(
        [windows[["window_start", "attack_frac", "attack", "label"]], normed],
        axis=1,
    )

    if scaler_path is not None:
        Path(scaler_path).parent.mkdir(parents=True, exist_ok=True)
        with open(scaler_path, "w") as fh:
            json.dump(
                {
                    "window_seconds": window_seconds,
                    "features": present,
                    "median": scaler["median"].tolist(),
                    "iqr": scaler["iqr"].tolist(),
                },
                fh,
            )
    return out, scaler


def _fit_robust_scaler(raw: pd.DataFrame, benign_mask: pd.Series) -> dict[str, np.ndarray]:
    benign = raw[benign_mask]
    if len(benign) == 0:
        benign = raw
    median = benign.median().to_numpy(float)
    q75 = benign.quantile(0.75).to_numpy(float)
    q25 = benign.quantile(0.25).to_numpy(float)
    iqr = np.clip(q75 - q25, 1e-9, None).astype(float)
    return {"median": median, "iqr": iqr}