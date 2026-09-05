"""Workstream 4 - explainability for the world-model forecast.

Two perspectives on every prediction:

  * Attention attribution: the LSTM's additive-attention weights show which
    historical windows (S_(t-k)..S_t) most influenced the next-state forecast.
  * SHAP attribution: a RandomForest attack classifier trained on the same
    canonical flow features explains which traffic features pushed a sample
    toward / away from the attack class.

Both feed the defender-facing demo (dashboard/).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestClassifier

from models.lstm_world import WorldModelLSTM
from training.forecast import build_state_matrix, load_model


def attention_attribution(
    checkpoint: str | Path,
    windows: pd.DataFrame,
    target_idx: int,
    seq_len: int,
) -> dict[str, object]:
    """Attention weights over the sequence ending at target_idx."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(checkpoint, device)
    states, attack, _ = build_state_matrix(windows)
    x = torch.from_numpy(states[target_idx - seq_len + 1 : target_idx + 1][None]).float().to(device)
    _, _, attn = model(x)
    weights = attn[0].detach().cpu().numpy()

    times = pd.to_datetime(windows["window_start"].to_numpy())
    selected = [
        {
            "window": str(times[i]),
            "attention": float(w),
            "gt_attack": int(attack[i]),
        }
        for i, w in zip(range(target_idx - seq_len + 1, target_idx + 1), weights)
    ]
    selected.sort(key=lambda r: r["attention"], reverse=True)
    return {
        "target_window": str(times[target_idx]),
        "forecast_next_attack": float(model.attack_probability(x).item()),
        "top_influential_windows": selected[: min(5, len(selected))],
    }


def shap_attribution(
    binary_csv: str | Path,
    n_estimators: int = 100,
    sample_index: int | None = None,
) -> dict[str, object]:
    """Train a RandomForest attack classifier and SHAP-explain a sample."""
    import shap

    df = pd.read_csv(binary_csv)
    feature_cols = [c for c in df.columns if c not in ("timestamp", "label", "attack")]
    X = df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    y = df["attack"]

    model = RandomForestClassifier(n_estimators=n_estimators, n_jobs=-1, random_state=42)
    model.fit(X, y)
    explainer = shap.TreeExplainer(model)

    def _explain(ix: int, name: str) -> dict[str, object]:
        sample = X.iloc[[ix]]
        values = explainer.shap_values(sample, check_additivity=False)
        sv = values[0] if isinstance(values, list) else values
        if sv.ndim > 2:
            sv = sv[:, :, -1]
        sv = np.asarray(sv).reshape(-1)
        rows = sorted(
            zip(feature_cols, sv.tolist()),
            key=lambda kv: -abs(kv[1]),
        )
        return {
            "name": name,
            "label": int(y.iloc[ix]),
            "label_meaning": "ATTACK" if int(y.iloc[ix]) else "BENIGN",
            "predicted": int(model.predict(sample)[0]),
            "top_features": [{"feature": f, "shap_value": round(v, 6)}
                             for f, v in rows[:10]],
        }

    n_attack = int(y.sum())
    attack_ix = int(y[y == 1].index[sample_index if sample_index is not None else 0])
    benign_ix = int(y[y == 0].index[0])
    return {
        "model": "RandomForest",
        "n_features": len(feature_cols),
        "samples": [_explain(attack_ix, "attack_sample"),
                    _explain(benign_ix, "benign_sample")],
    }


def run_explain(
    checkpoint: str | Path,
    windows_path: str | Path,
    binary_csv: str | Path,
    seq_len: int,
    out_dir: str | Path,
) -> None:
    windows = pd.read_csv(windows_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    first_attack = int(np.flatnonzero(windows["attack"].to_numpy() > 0)[0])
    target_idx = max(first_attack, seq_len)
    attn = attention_attribution(checkpoint, windows, target_idx, seq_len)
    (out / "explain_attention.json").write_text(json.dumps(attn, indent=2, default=str))

    shap_result = shap_attribution(binary_csv)
    (out / "explain_shap.json").write_text(json.dumps(shap_result, indent=2))

    print(f"[explain] attention -> {out / 'explain_attention.json'}")
    print(f"[explain] shap     -> {out / 'explain_shap.json'}")
    print(f"[explain] {attn['target_window']} -> forecast P(attack)={attn['forecast_next_attack']:.3f}")
    print("[explain] top influential windows:", [r["window"] for r in attn["top_influential_windows"]][:3])
    print("[explain] SHAP: attack sample top feature =",
          shap_result["samples"][0]["top_features"][0]["feature"])