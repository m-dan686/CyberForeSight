"""Workstream 6 - world model (LSTM) vs logistic-regression baseline.

Both models are asked the SAME forecasting question: given the network state
at window t, how likely is an attack in window t+1?  They are compared over
the same out-of-sample, chronologically-ordered horizon (the forecast
timeline produced by the LSTM world model).

Artifacts (-> models/):
  benchmark_metrics.json   accuracy/FPR/P/AUC for each model at threshold
  benchmark_compare.csv    per-window probabilities for both models
  benchmark_compare.png    probability step-lines vs ground-truth band
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler


def run_benchmark(
    args: object,
    cfg: dict,
    threshold: float = 0.6,
) -> int:
    pid, mid = cfg["data"]["processed_dir"], cfg["data"]["ml_dir"]
    save_dir = Path(cfg["training"]["save_dir"])
    save_dir.mkdir(parents=True, exist_ok=True)

    windows = pd.read_csv(f"{pid}/window_state.csv")
    transitions = pd.read_csv(f"{pid}/transitions.csv")
    timeline = pd.read_csv(f"{save_dir}/forecast_timeline.csv")

    state_cols = [c for c in windows.columns if c.startswith("state_")]
    # Ground truth for "attack in the NEXT window", aligned per transition row
    nxt = transitions[["window_start", "attack_t1"]].copy()
    nxt["attack_t1"] = nxt["attack_t1"].astype(int)
    probs = timeline[["window_start", "prob_next"]].copy()

    both = probs.merge(nxt, on="window_start", how="inner")
    keep = windows["window_start"].isin(both["window_start"])
    X_t = windows.loc[keep, state_cols].to_numpy()
    y_for = both["attack_t1"].to_numpy()
    horizon_ts = both["window_start"].to_numpy()
    if len(X_t) != len(both):
        print("[benchmark] state/target misalignment", file=sys.stderr)
        return 1

    n = len(X_t)
    train_sz = int(n * (1 - cfg["training"]["val_split"] - cfg["training"]["test_split"]))
    lr = LogisticRegression(max_iter=2000, C=0.1)
    lr.fit(X_t[:train_sz], y_for[:train_sz])

    lstm_prob = both["prob_next"].to_numpy()[train_sz:]
    lr_prob = lr.predict_proba(X_t[train_sz:])[:, 1]
    y_ev = y_for[train_sz:]
    horizon_ts = horizon_ts[train_sz:]

    lstm_auc = roc_auc_score(y_ev, lstm_prob) if y_ev.sum() and (1 - y_ev).sum() else float("nan")
    lr_auc = roc_auc_score(y_ev, lr_prob) if y_ev.sum() and (1 - y_ev).sum() else float("nan")

    def _summary(prob: np.ndarray) -> dict[str, float]:
        pred = (prob >= threshold).astype(int)
        tp = int(((pred == 1) & (y_ev == 1)).sum())
        fp = int(((pred == 1) & (y_ev == 0)).sum())
        fn = int(((pred == 0) & (y_ev == 1)).sum())
        return {
            "accuracy": round(accuracy_score(y_ev, pred), 4),
            "precision": round(tp / max(tp + fp, 1), 4),
            "recall": round(tp / max(tp + fn, 1), 4),
            "fpr": round(fp / max((y_ev == 0).sum(), 1), 4),
        }

    metrics = {
        "horizon_windows": int(n - train_sz),
        "n_infiltration_eval": int(y_ev.sum()),
        "threshold": threshold,
        "lstm_world_model": _summary(lstm_prob),
        "logistic_regression": _summary(lr_prob),
    }
    metrics["lstm_world_model"]["auc"] = round(lstm_auc, 4)
    metrics["logistic_regression"]["auc"] = round(lr_auc, 4)

    compare = pd.DataFrame(
        {
            "window_start": horizon_ts,
            "attack_next": y_ev,
            "lstm_prob": np.round(lstm_prob, 5),
            "lr_prob": np.round(lr_prob, 5),
        }
    )
    compare.to_csv(save_dir / "benchmark_compare.csv", index=False)
    (save_dir / "benchmark_metrics.json").write_text(json.dumps(metrics, indent=2))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(compare["window_start"], compare["lstm_prob"], color="#2563eb",
                lw=1.3, label="LSTM world model (forecast)")
        ax.plot(compare["window_start"], compare["lr_prob"], color="#16a34a",
                lw=1.3, ls="--", label="Logistic regression (window state)")
        ax.axhline(threshold, color="#dc2626", ls=":", lw=1, label=f"threshold {threshold}")
        ax.fill_between(compare["window_start"], 0, 1,
                        where=compare["attack_next"] == 1, color="#dc2626", alpha=0.2,
                        label="ground-truth infiltration window")
        ax.legend(loc="upper left", fontsize=8)
        ax.set_ylabel("P(attack in next window)")
        ax.set_title("WS6 - LSTM world model vs logistic-regression baseline (out-of-sample)")
        fig.tight_layout()
        fig.savefig(save_dir / "benchmark_compare.png", dpi=130)
        plt.close(fig)
    except ImportError:  # pragma: no cover
        pass

    print("[benchmark] out-of-sample horizon:", metrics["horizon_windows"], "windows,", metrics["n_infiltration_eval"], "infiltration")
    print(f"[benchmark] LSTM  acc={metrics['lstm_world_model']['accuracy']} fpr={metrics['lstm_world_model']['fpr']} auc={metrics['lstm_world_model']['auc']}")
    print(f"[benchmark] LR    acc={metrics['logistic_regression']['accuracy']} fpr={metrics['logistic_regression']['fpr']} auc={metrics['logistic_regression']['auc']}")
    print(f"[benchmark] metrics -> {save_dir / 'benchmark_metrics.json'}")
    print(f"[benchmark] compare -> {save_dir / 'benchmark_compare.csv'}")
    print(f"[benchmark] chart   -> {save_dir / 'benchmark_compare.png'}")
    return 0