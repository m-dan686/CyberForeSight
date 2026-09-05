"""K-step forward simulation + infiltration timeline (Workstream 3 forecast).

Two views are produced from the trained world model:
  1. Teacher-forced one-step timeline: p(t -> t+1 attack) over every window,
     aligned to the ground-truth infiltration block - gives FPR and the
     earliest-flag / lead-time signal before an attack actually starts.
  2. Autoregressive rollout: from a chosen start window S_t, repeatedly push
     predicted states back through the LSTM for K steps (S_t -> S_(t+1) ->
     ... -> S_(t+K)) recording the attack probability each step. This is the
     "infiltration scenario" the defender watches unfold before it happens.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from models.lstm_world import WorldModelLSTM


def load_model(checkpoint: str | Path, device: torch.device) -> WorldModelLSTM:
    ckpt = torch.load(checkpoint, map_location=device, weights_only=False)
    cfg = ckpt["config"]
    model = WorldModelLSTM(
        input_dim=cfg["input_dim"],
        hidden_dim=cfg["hidden_size"],
        num_layers=cfg["num_layers"],
        dropout=cfg["dropout"],
    )
    model.load_state_dict(ckpt["state_dict"])
    model.to(device).eval()
    return model


def build_state_matrix(windows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    states = np.stack(
        [windows[c].to_numpy(float) for c in windows.columns if c.startswith("state_")],
        axis=1,
    )
    attack = windows["attack"].to_numpy(int)
    frac = windows["attack_frac"].to_numpy(float)
    return states.astype(np.float32), attack, frac


def one_step_timeline(
    model: WorldModelLSTM,
    states: np.ndarray,
    seq_len: int,
    device: torch.device,
    threshold: float = 0.6,
) -> pd.DataFrame:
    """Teacher-forced next-window attack probability for every window."""
    model.eval()
    probs = []
    with torch.no_grad():
        for i in range(seq_len - 1, states.shape[0] - 1):
            x = torch.from_numpy(states[i - seq_len + 1 : i + 1][None]).to(device)
            prob = model.attack_probability(x).item()
            probs.append(prob)
    prob = np.asarray(probs, dtype=np.float64)
    return pd.DataFrame(
        {
            "prob_next": prob,
            "flagged": (prob >= threshold).astype(int),
        }
    )


def rollout_k(
    model: WorldModelLSTM,
    states: np.ndarray,
    start_idx: int,
    k: int,
    seq_len: int,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    """Autoregressive rollout: predicted states and attack probs for K steps."""
    model.eval()
    window = torch.from_numpy(states[start_idx - seq_len + 1 : start_idx + 1][None]).float().to(device)
    pred_states = []
    probs = []
    with torch.no_grad():
        for _ in range(k):
            next_state, _, _ = model(window)
            pred_states.append(next_state[0].cpu().numpy())
            probs.append(model.attack_probability(window).item())
            window = torch.cat([window[:, 1:, :], next_state.unsqueeze(1)], dim=1)
    return np.asarray(pred_states), np.asarray(probs)


def infiltration_lead_time(
    df: pd.DataFrame,
    attack_frac: np.ndarray,
    threshold: float,
    seq_len: int,
) -> dict[str, object]:
    """Earliest flag before the actual infiltration block starts."""
    gt = attack_frac > 0
    lead = df.assign(gt_attack=gt[seq_len - 1 : -1])
    first_attack_i = int(np.argmax(gt)) if gt.any() else -1
    flagged_pre = lead[(lead["flagged"] == 1) & (lead["gt_attack"] == 0)]
    earliest_pre = int(flagged_pre.index.min()) if len(flagged_pre) else -1
    earliest_pre_abs = earliest_pre + (seq_len - 1)
    return {
        "threshold": threshold,
        "first_attack_window_idx": first_attack_i,
        "first_attack_ts": None,
        "earliest_pre_flag_idx": earliest_pre_abs,
        "lead_minutes": (first_attack_i - earliest_pre_abs) if (earliest_pre_abs != -1 and first_attack_i != -1) else None,
        "pre_flag_count": int(len(flagged_pre)),
    }


def plot_forecast(
    timeline: pd.DataFrame,
    rollout: pd.DataFrame,
    start_window: str,
    out_path: str | Path,
    threshold: float = 0.6,
) -> None:
    """Two-panel chart: teacher-forced threat timeline + K-step rollout."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:  # pragma: no cover - matplotlib optional for demo
        return

    gt_attack = timeline["attack_frac"] > 0
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 6), sharex=False, gridspec_kw={"height_ratios": [2, 1]}
    )

    ax1.plot(timeline["window_start"], timeline["prob_next"],
             color="#2563eb", lw=1.4, label="Predicted infiltration probability (next window)")
    ax1.axhline(threshold, color="#dc2626", ls="--", lw=1,
                label=f"Threat threshold ({threshold})")
    ax1.fill_between(timeline["window_start"], 0, timeline["prob_next"],
                     where=gt_attack, color="#dc2626", alpha=0.25,
                     label="Ground-truth infiltration")
    ax1.set_ylabel("P(attack | next window)")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.set_title("CyberForeSight - infiltration probability timeline (CIC-IDS-2018)")

    ax2.bar(np.arange(1, len(rollout) + 1), rollout["attack_probability"],
            color="#f59e0b", alpha=0.85)
    ax2.axhline(threshold, color="#dc2626", ls="--", lw=1)
    ax2.set_xlabel("Rollout step (minute ahead)")
    ax2.set_ylabel("P(attack)")
    ax2.set_title(f"K-step autoregressive rollout from S_t ({start_window})", fontsize=9)

    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def run_forecast(
    windows_path: str | Path,
    checkpoint: str | Path,
    seq_len: int,
    k_steps: int,
    threshold: float,
    out_dir: str | Path,
    start_idx: int | None = None,
) -> pd.DataFrame:
    windows = pd.read_csv(windows_path)
    windows["window_start"] = pd.to_datetime(windows["window_start"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = load_model(checkpoint, device)
    states, attack, frac = build_state_matrix(windows)

    timeline = one_step_timeline(model, states, seq_len, device, threshold)
    timeline = timeline.iloc[: attack.size - seq_len]  # drop trailing
    timeline["window_start"] = windows["window_start"].to_numpy()[seq_len - 1 : -1].copy()
    timeline["attack_frac"] = frac[seq_len - 1 : -1]
    timeline["attack"] = attack[seq_len - 1 : -1]

    start_idx = start_idx if start_idx is not None else max(0, int(np.argmax(frac > 0)) - 1)
    pred_states, probs = rollout_k(model, states, start_idx, k_steps, seq_len, device)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    timeline_path = out / "forecast_timeline.csv"
    timeline.to_csv(timeline_path, index=False)

    rollout_path = out / "forecast_rollout.csv"
    pd.DataFrame(
        {
            "step": np.arange(1, k_steps + 1),
            "minutes_ahead": np.arange(k_steps),
            "attack_probability": probs,
        }
    ).to_csv(rollout_path, index=False)

    info = infiltration_lead_time(timeline, frac, threshold, seq_len)
    if (first_idx := info["first_attack_window_idx"]) != -1:
        info["first_attack_ts"] = str(windows["window_start"].to_numpy()[first_idx])
    info["start_window"] = str(windows["window_start"].to_numpy()[start_idx])
    info["k_steps"] = k_steps
    info["seq_len"] = seq_len
    (out / "forecast_info.json").write_text(json.dumps(info, indent=2, default=str))

    rollout_df = pd.read_csv(rollout_path)
    plot_forecast(timeline, rollout_df, info["start_window"], out / "forecast_timeline.png", threshold)
    print(f"[forecast] chart -> {out / 'forecast_timeline.png'}")

    print(f"[forecast] timeline -> {timeline_path}")
    print(f"[forecast] rollout (start {info['start_window']}, k={k_steps}) -> {rollout_path}")
    print(f"[forecast] info -> {out / 'forecast_info.json'}")
    return timeline