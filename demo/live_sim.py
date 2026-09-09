"""CyberForeSight — Live Attack Lab (realtime attack-simulation feed).

Drives the trained world model in real time against a *replayed* traffic-state
stream: the quiet baseline and the injected infiltration burst are genuine
CIC-IDS2018 Infiltration-day window states (the exact same states the model was
scored on offline), so every published probability is a real forward pass, not
fiction. The "dummy attack" injects the actual infiltration ramp + onset burst
on a trigger; the K-step forecast is a live autoregressive rollout from the
model (S_t -> hat S_{t+1} -> ... -> hat S_{t+K}).

Protocol: emits one JSON object per line on stdout.
  {"type":"ready",  ...}
  {"type":"state",  "t":n, "phase":.., "window_start":.., "prob":.., "flag":..,
                    "stage":.., "stage_confidence":.., "stage_technique":..,
                    "rollout":[ {k,prob,stage} ... ]}      (rollout = live forecast)
Accepts control lines on stdin (JSON):
  {"cmd":"trigger"}   -> inject the infiltration ramp + onset burst
  {"cmd":"reset"}     -> back to idle baseline
  {"cmd":"standby"}   -> pause emitting (hold context)

Run headless (no pacing, useful for CI/test): --tick 0 --max <ticks> [--auto-trigger-after <n>]
"""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from detection.stage_mapping import score_stages  # noqa: E402
from training.forecast import build_state_matrix, load_model, rollout_k  # noqa: E402

MODELS_DIR = ROOT / "models"
PROCESSED_DIR = ROOT / "data" / "processed"

DEFAULT_TICK = 1.0          # wall-clock seconds per replayed window
THRESHOLD = 0.6             # must match configs/world_model.yaml forecasting.threat_threshold
K_ROLLOUT = 8               # must match configs/world_model.yaml forecasting.k_steps


def _segment_bounds(windows: np.ndarray, t_start: str, t_end: str) -> list[int]:
    """Source-row indices whose window_start is in [t_start, t_end)."""
    return [i for i, ts in enumerate(windows) if t_start <= ts < t_end]


def build_segments() -> dict[str, list[int]]:
    ws = _typed_windows()
    ts = ws["window_start"].astype(str)
    idle = _segment_bounds(ts, "2018-03-01 01:10", "2018-03-01 01:47")
    ramp = _segment_bounds(ts, "2018-03-01 01:47", "2018-03-01 02:00")
    attack = _segment_bounds(ts, "2018-03-01 02:00", "2018-03-01 02:12")
    for name, seg in (("idle", idle), ("ramp", ramp), ("attack", attack)):
        print(f"[livesim] segment {name}: {len(seg)} windows "
              f"{ts[seg[0]] if seg else '-'}..{ts[seg[-1]] if seg else '-'}",
              file=sys.stderr, flush=True)
    if not idle or not ramp or not attack:
        raise SystemExit(f"[livesim] could not carve live-lab segments "
                         f"(idle={len(idle)} ramp={len(ramp)} attack={len(attack)})")
    return {"idle": idle, "ramp": ramp, "attack": attack}


_WS: dict = {}


def _typed_windows() -> dict:
    if not _WS:
        import pandas as pd
        df = pd.read_csv(PROCESSED_DIR / "window_state.csv")
        df["window_start"] = pd.to_datetime(df["window_start"])
        _WS["window_start"] = df["window_start"].dt.strftime("%Y-%m-%d %H:%M:%S").to_numpy()
        _WS["attack"] = df["attack"].to_numpy(int)
        _WS["attack_frac"] = df["attack_frac"].to_numpy(float)
    return _WS


class LiveSim:
    # csv window_indices (data/processed/window_state.csv) for each phase.
    # 01:10..01:46 quiet baseline | 01:47..01:59 infiltration ramp | 02:00..02:11 onset burst
    SEG_BOUNDS = {"idle": (10, 47), "ramp": (47, 60), "attack": (60, 72)}

    def __init__(self, tick: float, k: int, threshold: float) -> None:
        self.tick = tick
        self.k = k
        self.threshold = threshold
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        ckpt = torch.load(Path(MODELS_DIR) / "world_model_transformer.pt",
                          map_location=self.device, weights_only=False)
        self.seq_len = int(ckpt.get("config", {}).get("seq_len", 10))
        self.model = load_model(Path(MODELS_DIR) / "world_model_transformer.pt", self.device)
        self.phase = "idle"
        self.current = self.SEG_BOUNDS["idle"][0] - 1  # next tick emits the first idle window
        self.states = build_state_matrix(
            __import__("pandas").read_csv(PROCESSED_DIR / "window_state.csv"))[0]
        self.feature_names = [c.replace("state_", "") for c in
                              self._window_cols()]
        self.observer = {x: 0 for x in ("emitted", "flagged", "attack_injected")}
        self.pending: queue.Queue = queue.Queue()

    def _window_cols(self) -> list[str]:
        import pandas as pd
        head = pd.read_csv(PROCESSED_DIR / "window_state.csv", nrows=1)
        return [c for c in head.columns if c.startswith("state_")]

    # -- control ----------------------------------------------------------
    def on_command(self, cmd: dict) -> None:
        kind = cmd.get("cmd")
        if kind == "trigger":
            if self.phase == "idle":
                print(json.dumps({"type": "ack", "cmd": "trigger",
                                  "note": "injecting infiltration ramp + onset burst"}), flush=True)
                self.phase, self.current = "ramp", self.SEG_BOUNDS["ramp"][0] - 1
            else:
                print(json.dumps({"type": "ack", "cmd": "trigger", "skipped": True,
                                  "phase": self.phase}), flush=True)
        elif kind == "reset":
            self.phase = "idle"
            self.current = self.SEG_BOUNDS["idle"][0] - 1
            print(json.dumps({"type": "ack", "cmd": "reset"}), flush=True)

    # -- context handling -------------------------------------------------
    def _next_context(self) -> list[int] | None:
        """Return the contiguous seq_len window indices ending at the next tick's
        window (the exact context used for offline scoring), or None once a
        one-shot phase exhausts (run() then returns to baseline)."""
        lo, hi = self.SEG_BOUNDS[self.phase]
        if self.current < lo - 1:
            self.current = lo - 1
        nxt = self.current + 1
        if nxt >= hi:
            if self.phase == "idle":
                self.current = lo - 1          # loop quiet baseline while waiting
            elif self.phase == "ramp":
                self.phase = "attack"          # ramp ends exactly at the onset burst
                self.current = self.SEG_BOUNDS["attack"][0] - 1
            else:
                print(json.dumps({"type": "ack", "cmd": "return-to-baseline"}), flush=True)
                self.phase = "idle"
                self.current = self.SEG_BOUNDS["idle"][0] - 1
            return None
        self.current = nxt
        start = max(0, nxt - (self.seq_len - 1))
        return list(range(start, nxt + 1))

    # -- scoring ----------------------------------------------------------
    def _score(self, ctx: list[int]):
        x = torch.from_numpy(self.states[ctx][None]).float().to(self.device)
        with torch.no_grad():
            prob = float(self.model.attack_probability(x).item())
            next_state, _, _ = self.model(x)
            step_stages = score_stages(
                next_state[0].cpu().numpy().astype(np.float32),
                self.feature_names, prob,
            )
            rollout: list[dict] = []
            if self.phase in ("ramp", "attack"):
                window = x
                for _ in range(self.k):
                    ns, _, _ = self.model(window)
                    rp = float(self.model.attack_probability(window).item())
                    rstage = score_stages(ns[0].cpu().numpy().astype(np.float32),
                                          self.feature_names, rp)
                    rollout.append({"k": len(rollout) + 1,
                                    "prob": round(rp, 4),
                                    "stage": rstage["stage"],
                                    "stage_id": rstage["stage_id"],
                                    "confidence": round(rstage["confidence"], 3)})
                    window = torch.cat([window[:, 1:, :], ns.unsqueeze(1)], dim=1)
        return prob, step_stages, rollout

    def _emit(self, ctx: list[int]) -> None:
        ws = _typed_windows()
        idx = ctx[-1]
        prob, stage, rollout = self._score(ctx)
        flag = float(prob) >= self.threshold
        injected = int(ws["attack"][idx])
        self.observer["emitted"] += 1
        self.observer["flagged"] += int(flag)
        self.observer["attack_injected"] += injected
        out = {
            "type": "state",
            "t": self.observer["emitted"],
            "phase": self.phase,
            "window_start": str(ws["window_start"][idx]),
            "source_idx": int(idx),
            "attack_injected": injected,
            "attack_frac": round(float(ws["attack_frac"][idx]), 4),
            "prob": round(prob, 4),
            "flag": int(flag),
            "threshold": self.threshold,
            "stage": stage["stage"],
            "stage_id": stage["stage_id"],
            "stage_confidence": round(stage["confidence"], 3),
            "stage_technique": stage["technique"],
            "rollout": rollout,
        }
        print(json.dumps(out), flush=True)

    def run(self, max_ticks: int | None, auto_trigger_after: int | None) -> None:
        n = 0
        while max_ticks is None or n < max_ticks:
            if auto_trigger_after is not None and n == auto_trigger_after:
                self.on_command({"cmd": "trigger"})
            control: list[dict] = []
            try:
                while True:
                    control.append(self.pending.get_nowait())
            except queue.Empty:
                pass
            for c in control:
                self.on_command(c)
            ctx = self._next_context()
            if ctx is None:
                time.sleep(0.1)          # one-shot phase just exhausted -> baseline next loop
                continue
            self._emit(ctx)
            n += 1
            if self.tick > 0:
                time.sleep(self.tick)


def stdin_reader(q: queue.Queue) -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            q.put(json.loads(line))
        except json.JSONDecodeError:
            try:
                q.put({"cmd": line})
            except Exception:
                pass


def main() -> int:
    p = argparse.ArgumentParser(description="CyberForeSight Live Attack Lab feed")
    p.add_argument("--tick", type=float, default=DEFAULT_TICK,
                   help="seconds per replayed window (0 = headless fast mode)")
    p.add_argument("--max", type=int, default=None, dest="max_ticks",
                   help="stop after N emitted windows (default: run forever)")
    p.add_argument("--auto-trigger-after", type=int, default=None,
                   help="inject the dummy attack after N windows without stdin")
    p.add_argument("--k", type=int, default=K_ROLLOUT, help="rollout horizon")
    p.add_argument("--threshold", type=float, default=THRESHOLD)
    args = p.parse_args()

    sim = LiveSim(tick=args.tick, k=args.k, threshold=args.threshold)
    print(json.dumps({"type": "ready",
                      "model": "temporal-transformer world model",
                      "seq_len": sim.seq_len,
                      "k": sim.k,
                      "threshold": sim.threshold,
                      "device": str(sim.device),
                      "phase": "idle",
                      "segments": {k: f"{v[0]=}..{v[1]=}" for k, v in LiveSim.SEG_BOUNDS.items()}}), flush=True)

    q: queue.Queue = queue.Queue()
    t = threading.Thread(target=stdin_reader, args=(q,), daemon=True)
    t.start()
    sim.pending = q
    sim.run(args.max_ticks, args.auto_trigger_after)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        raise SystemExit(0)