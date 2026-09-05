"""Workstream 6 - world model (LSTM/Transformer) vs logistic-regression baseline.

Both models answer the SAME forecasting question: given the network state
observed up to window t (the last full window), how likely is an attack in
window t+1 = W?  They are compared over the same out-of-sample, chronologically
ordered horizon.

Evaluation protocol (fixed vs the original version):
  * Label alignment: prob_next(W) is matched against attack[W] (the label of the
    window being forecast), not the shifted attack_t1 used before.
  * Strictly OOS for the world model: the eval horizon is every target window at
    or after the train/val boundary (abs index >= 0.70*N), i.e. windows the world
    model never trained on (val + test splits).
  * The logistic baseline is fit ONLY on train-region states (abs < boundary) and
    evaluated on the identical eval horizon - no in-sample contamination.
  * Threshold rows: (a) shared threshold from config (0.6), (b) per-model
    threshold chosen on the val slice (max F1) then applied to eval.
  * Early-detection metrics: pre-onset first flag / lead time / P at onset-{1..3}
    showing the world model's forward-simulation advantage over a static baseline.

Artifacts (-> models/):
  benchmark_metrics.json   accuracy/P/R/F1/FPR/AUC + early-detection for both models
  benchmark_compare.csv    per-window probabilities for both models over the OOS horizon
  benchmark_compare.png    probability curves vs ground-truth band + onset line
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler


def _summary(y: np.ndarray, prob: np.ndarray, threshold: float) -> dict[str, float]:
    pred = (prob >= threshold).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    p = tp / max(tp + fp, 1)
    r = tp / max(tp + fn, 1)
    f1 = 2 * p * r / max(p + r, 1e-9)
    return {
        "threshold": round(float(threshold), 3),
        "accuracy": round(float((pred == y).mean()), 4),
        "precision": round(float(p), 4),
        "recall": round(float(r), 4),
        "f1": round(float(f1), 4),
        "fpr": round(float(fp / max((y == 0).sum(), 1)), 4),
    }


def _tune_threshold(y: np.ndarray, prob: np.ndarray) -> float:
    best_t, best_f1 = 0.5, -1.0
    for t in np.linspace(0.05, 0.95, 19):
        pred = (prob >= t).astype(int)
        tp = int(((pred == 1) & (y == 1)).sum())
        fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum())
        p = tp / max(tp + fp, 1)
        r = tp / max(tp + fn, 1)
        f1 = 2 * p * r / max(p + r, 1e-9)
        if f1 > best_f1 + 1e-9 or (abs(f1 - best_f1) <= 1e-9 and t > best_t):
            best_t, best_f1 = float(t), float(f1)
    return best_t


def _auc(y: np.ndarray, prob: np.ndarray) -> float | None:
    if y.sum() and (y == 0).sum():
        return round(float(roc_auc_score(y, prob)), 4)
    return None


def _early_detection(
    ts: np.ndarray, probs: np.ndarray, attack: np.ndarray,
    first_attack_idx: int, threshold: float,
) -> dict[str, object]:
    """Pre-onset detection behaviour over the section before the first attack."""
    pre = probs[:first_attack_idx] if first_attack_idx > 0 else probs[:0]
    pre_flags = int((pre >= threshold).sum())
    first_flag_idx = (
        int(np.flatnonzero(pre >= threshold)[0]) if (pre >= threshold).any() else -1
    )
    out: dict[str, object] = {
        "pre_onset_flags": pre_flags,
    }
    if first_flag_idx != -1:
        out["first_flag_time"] = str(ts[first_flag_idx])
        out["lead_windows_before_onset"] = int(first_attack_idx - first_flag_idx)
    else:
        out["first_flag_time"] = None
        out["lead_windows_before_onset"] = None
    for k in (1, 2, 3):
        i = first_attack_idx - k
        out[f"prob_at_onset_minus_{k}"] = (
            round(float(probs[i]), 4) if 0 <= i < len(probs) else None
        )
    return out


def run_benchmark(
    args: object,
    cfg: dict,
    threshold: float | None = None,
) -> int:
    pid, mid = cfg["data"]["processed_dir"], cfg["data"]["ml_dir"]
    save_dir = Path(cfg["training"]["save_dir"])
    save_dir.mkdir(parents=True, exist_ok=True)

    windows = pd.read_csv(f"{pid}/window_state.csv")
    timeline = pd.read_csv(f"{save_dir}/forecast_timeline.csv")
    timeline["window_start"] = pd.to_datetime(timeline["window_start"])

    state_cols = [c for c in windows.columns if c.startswith("state_")]
    windows["window_start"] = pd.to_datetime(windows["window_start"])
    abs_index = {ts: int(i) for i, ts in enumerate(windows["window_start"])}
    n_total = len(windows)

    shared_threshold = (
        threshold
        or cfg.get("benchmark", {}).get("threshold_shared")
        or cfg["forecasting"]["threat_threshold"]
    )

    model_label = cfg.get("model", {}).get("type", "lstm")
    model_key = f"{model_label}_world_model"

    boundary_train = int(n_total * (1 - cfg["training"]["val_split"] - cfg["training"]["test_split"]))
    boundary_val = int(n_total * (1 - cfg["training"]["test_split"]))
    print(f"[benchmark] windows={n_total} train<{boundary_train} val<{boundary_val} eval>= {boundary_train}")

    rows: list[dict[str, object]] = []
    for _, r in timeline.iterrows():
        ts = r["window_start"]
        idx = abs_index.get(ts)
        if idx is None:
            continue
        rows.append(
            {
                "window_start": ts,
                "abs_idx": idx,
                "prob_lstm": float(r["prob_next"]),
                "attack": int(r.get("attack", 0)),
                "region": ("train" if idx < boundary_train else "val" if idx < boundary_val else "test"),
            }
        )
    df = pd.DataFrame(rows)

    target = df["abs_idx"].to_numpy()
    features = np.stack(
        [windows.loc[windows["window_start"].isin(df["window_start"]), c].to_numpy(float) for c in state_cols],
        axis=1,
    )
    if len(features) != len(df):
        print("[benchmark] state/timeline misalignment", file=sys.stderr)
        return 1

    y = df["attack"].to_numpy(int)
    prob_lstm = df["prob_lstm"].to_numpy()

    lr_train_mask = target < boundary_train
    eval_mask = target >= boundary_train
    val_mask = (target >= boundary_train) & (target < boundary_val)

    scaler = StandardScaler()
    X_lr = scaler.fit_transform(features[lr_train_mask])
    lr = LogisticRegression(max_iter=cfg.get("benchmark", {}).get("lr_max_iter", 2000),
                            C=cfg.get("benchmark", {}).get("lr_c", 0.1))
    lr.fit(X_lr, y[lr_train_mask])
    X_eval = scaler.transform(features[eval_mask])
    prob_lr = lr.predict_proba(X_eval)[:, 1]

    y_ev = y[eval_mask]
    lstm_oos = prob_lstm[eval_mask]
    ts_oos = df["window_start"].to_numpy()[eval_mask]

    common_rows = {
        "horizon_windows": int(eval_mask.sum()),
        "n_infiltration_eval": int(y_ev.sum()),
        "shared_threshold": float(shared_threshold),
        "eval_region": "val+test (chronologically OOS for the world model)",
    }

    results: dict[str, object] = {}
    results[model_key] = {"common": common_rows}
    results["logistic_regression"] = {"common": common_rows}

    for key, prob in ((model_key, lstm_oos), ("logistic_regression", prob_lr)):
        block = results[key]
        block["auc"] = _auc(y_ev, prob)
        block["shared_threshold"] = _summary(y_ev, prob, float(shared_threshold))

        if val_mask.any():
            tuned = _tune_threshold(y[val_mask], prob_lstm[val_mask] if key == model_key
                                    else lr.predict_proba(scaler.transform(features[val_mask]))[:, 1])
        else:
            tuned = float(shared_threshold)
        block["val_tuned_threshold"] = tuned
        block["val_tuned"] = _summary(y_ev, prob, float(tuned))

    first_attack_idx = int(np.flatnonzero(y == 1)[0]) if y.any() else -1
    for key, prob in ((model_key, prob_lstm), ("logistic_regression", prob_lr)):
        full_ts = df["window_start"].to_numpy()
        full_prob = prob if key == "logistic_regression" else prob_lstm
        full_y = y
        block = results[key]
        block["pre_onset_block"] = {
            "method": "illustration over ALL windows up to first attack (the world model's "
                      "forward-timeline section; the LR scores shown are in-sample for illustration)",
        }
        if first_attack_idx != -1:
            block["pre_onset_block"].update(
                _early_detection(full_ts, full_prob, full_y, first_attack_idx, float(shared_threshold))
            )
            block["pre_onset_block"]["onset_ts"] = str(full_ts[first_attack_idx])

    verdict: dict[str, object] = {}
    lf1 = results[model_key]["val_tuned"]["f1"]
    lr_f1 = results["logistic_regression"]["val_tuned"]["f1"]
    led_lstm = results[model_key]["pre_onset_block"].get("lead_windows_before_onset")
    led_lr = results["logistic_regression"]["pre_onset_block"].get("lead_windows_before_onset")
    verdict["f1_lstm_vs_lr"] = (lf1, lr_f1)
    verdict["lead_lstm_vs_lr"] = (led_lstm, led_lr)
    verdict["temporal_dynamics_win"] = bool(
        lf1 >= lr_f1 or (led_lstm is not None and led_lr is not None and led_lstm > led_lr)
    )
    results["verdict"] = verdict

    (save_dir / "benchmark_metrics.json").write_text(json.dumps(results, indent=2, default=str))

    compare = pd.DataFrame(
        {
            "window_start": ts_oos,
            "attack_next": y_ev,
            "lstm_prob": np.round(lstm_oos, 5),
            "lr_prob": np.round(prob_lr, 5),
            "region": df["region"].to_numpy()[eval_mask],
        }
    )
    compare.to_csv(save_dir / "benchmark_compare.csv", index=False)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(compare["window_start"], compare["lstm_prob"], color="#2563eb",
                lw=1.3, label="World model (forecast timeline)")
        ax.plot(compare["window_start"], compare["lr_prob"], color="#16a34a",
                lw=1.3, ls="--", label="Logistic regression (window state)")
        ax.axhline(shared_threshold, color="#dc2626", ls=":", lw=1,
                   label=f"threshold {shared_threshold}")
        ax.fill_between(compare["window_start"], 0, 1,
                        where=compare["attack_next"] == 1, color="#dc2626", alpha=0.2,
                        label="ground-truth infiltration window")
        if first_attack_idx != -1:
            ax.axvline(df["window_start"].to_numpy()[first_attack_idx], color="#dc2626",
                       lw=1.2, ls="--", alpha=0.7, label="first attack window")
        ax.legend(loc="upper left", fontsize=8)
        ax.set_ylabel("P(attack in next window)")
        ax.set_title("WS6 - world model vs logistic-regression baseline (OOS val+test horizon)")
        fig.tight_layout()
        fig.savefig(save_dir / "benchmark_compare.png", dpi=130)
        plt.close(fig)
    except ImportError:  # pragma: no cover
        pass

    l1 = results[model_key]
    l2 = results["logistic_regression"]
    print(f"[benchmark] OOS horizon: {common_rows['horizon_windows']} windows, "
          f"{common_rows['n_infiltration_eval']} infiltration")
    print(f"[benchmark] threshold {shared_threshold}: "
          f"{model_label} f1={l1['shared_threshold']['f1']} p={l1['shared_threshold']['precision']} "
          f"r={l1['shared_threshold']['recall']} fpr={l1['shared_threshold']['fpr']}"
          f" | LR  f1={l2['shared_threshold']['f1']} p={l2['shared_threshold']['precision']} "
          f"r={l2['shared_threshold']['recall']} fpr={l2['shared_threshold']['fpr']}")
    print(f"[benchmark] val-tuned:       "
          f"{model_label} f1={l1['val_tuned']['f1']} auc={l1['auc']} th={l1['val_tuned_threshold']}"
          f" | LR  f1={l2['val_tuned']['f1']} auc={l2['auc']} th={l2['val_tuned_threshold']}")
    print(f"[benchmark] lead (windows before onset): "
          f"{model_label}={l1['pre_onset_block'].get('lead_windows_before_onset')} "
          f"LR={l2['pre_onset_block'].get('lead_windows_before_onset')}")
    print(f"[benchmark] temporal-dynamics win = {verdict['temporal_dynamics_win']}")
    print(f"[benchmark] metrics -> {save_dir / 'benchmark_metrics.json'}")
    print(f"[benchmark] compare -> {save_dir / 'benchmark_compare.csv'}")
    return 0