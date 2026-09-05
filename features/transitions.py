"""Transitions: build ground-truth S_t -> S_t+1 training targets.

Reads the windowed state matrix and emits a transitions table where each row
is one training example: (window index, timestamp, state at t, next-state
target at t+1, attack/infiltration-onset labels).  This is the supervised
signal the world model learns P(S_t+1 | S_t) from.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def build_transitions(
    windows: pd.DataFrame,
    k_steps: int = 1,
    existence_cols: list[str] | None = None,
) -> pd.DataFrame:
    """Convert the window state matrix into S_t -> S_t+1 transition rows.

    Each output row corresponds to window index i and contains:
      idx, window_start, attack_t, attack_t1, onset_t1, label_t,
      state_* (window i), target_* (window i + k_steps).
    onset_t1 == 1 marks the first window where an attack begins (t benign,
    t+1 attacking) - the "infiltration onset" event we forecast ahead of time.
    """
    windows = windows.reset_index(drop=True)
    state_cols = [c for c in windows.columns if c.startswith("state_")]

    shifted = windows.shift(-k_steps)
    valid = windows.index < (len(windows) - k_steps)

    t = windows[valid]
    t1 = shifted[valid]

    out = pd.DataFrame(index=t.index)
    out["idx"] = t.index.values
    out["window_start"] = t["window_start"].values
    out["attack_t"] = t["attack"].values.astype(np.int8)
    out["attack_t1"] = t1["attack"].values.astype(np.int8)
    out["onset_t1"] = ((out["attack_t"] == 0) & (out["attack_t1"] == 1)).astype(np.int8)
    out["label_t"] = t["label"].values

    for c in state_cols:
        out[f"target_{c}"] = t1[c].values.astype(np.float32)

    if existence_cols is None:
        existence_cols = ["flow_count", "dst_port_uniq"]
    for c in existence_cols:
        src = f"state_{c}"
        if src in state_cols:
            out[f"ex_{c}_t"] = t1[src].ne(0).astype(np.int8)

    return out.reset_index(drop=True)


def summarize(windows: pd.DataFrame, transitions: pd.DataFrame) -> dict[str, object]:
    """Compact summary of the windowed dataset for pipeline logging."""
    attacks = windows["attack"].astype(int)
    onsets = int(transitions["onset_t1"].sum())
    return {
        "windows": len(windows),
        "attack_windows": int(attacks.sum()),
        "attack_frac_windows": float(attacks.mean()),
        "transitions": len(transitions),
        "onset_events": onsets,
        "state_dim": int(sum(1 for c in windows.columns if c.startswith("state_"))),
    }