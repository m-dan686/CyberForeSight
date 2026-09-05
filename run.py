#!/usr/bin/env python
"""
CyberForeSight - AI-based Network Attack Forecasting (SIH-26153)
Entry point. Use the bundled .venv interpreter to run.

Usage:
    .venv\\Scripts\\python run.py --stage features|train|forecast|benchmark
    .venv\\Scripts\\python run.py --stage train     --config configs/world_model.yaml
    .venv\\Scripts\\python run.py --stage forecast  --snapshot data/processed/window_state.csv

Stages (Workstreams):
    features   - build the flow/packet feature extraction pipeline (Workstream 2)
    train      - train the temporal world model (LSTM) (Workstream 3)
    forecast   - run K-step model-based rollout + infiltration scenario (Workstream 3)
    explain    - attention / SHAP feature attribution (Workstream 4)
    demo       - launch the offline Streamlit demo (Workstream 5)
    benchmark  - compare world model vs logistic regression baseline (Workstream 6)
"""
import argparse
import sys
from pathlib import Path


def _load_config(path: str) -> dict:
    try:
        import yaml as _yaml

        return _yaml.safe_load(Path(path).read_text())
    except Exception as exc:  # noqa: BLE001 - config is optional
        print(f"warning: cannot read config {path}: {exc}", file=sys.stderr)
        return {
            "data": {
                "raw_dir": "data/raw",
                "processed_dir": "data/processed",
                "ml_dir": "data/ml",
            },
            "windowing": {"window_seconds": 60},
        }


def run_features(args: argparse.Namespace) -> int:
    """Workstream 2: raw CIC flow CSV -> canonical flows -> windows -> transitions."""
    from features.extract_flow import build_flows_ml_datasets, extract_flow_csv
    from features.transitions import build_transitions, summarize
    from features.window import build_windows

    cfg = _load_config(args.config)
    window_seconds = args.window_seconds or cfg["windowing"]["window_seconds"]

    if args.csv:
        csv_path = Path(args.csv)
    else:
        raw = list(Path(cfg["data"]["raw_dir"]).glob("*.csv"))
        if not raw:
            print(
                "no CSV found in data/raw - pass --csv /path/file.csv or download a day file first",
                file=sys.stderr,
            )
            return 1
        csv_path = raw[0]

    print(f"[features] source: {csv_path}")
    flows = extract_flow_csv(csv_path, source_name=csv_path.stem)
    print(f"[features] flows: {len(flows):,} rows, columns: {flows.shape[1]}")

    out_dir = Path(cfg["data"]["processed_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    flows_path = out_dir / "flows_canonical.csv"
    flows.to_csv(flows_path, index=False)
    print(f"[features] canonical flows -> {flows_path}")

    build_flows_ml_datasets(flows, cfg["data"]["ml_dir"])

    scaler_path = out_dir / "scaler.json"
    windows, _ = build_windows(flows, window_seconds=window_seconds, scaler_path=scaler_path)
    windows_path = out_dir / "window_state.csv"
    windows.to_csv(windows_path, index=False)
    print(f"[features] windowed states ({window_seconds}s) -> {windows_path}")

    transitions = build_transitions(windows, k_steps=1)
    transitions_path = out_dir / "transitions.csv"
    transitions.to_csv(transitions_path, index=False)
    print(f"[features] transitions (S_t -> S_t+1) -> {transitions_path}")

    summary = summarize(windows, transitions)
    print("[features] summary:")
    for k, v in summary.items():
        print(f"    {k}: {v}")
    return 0


def run_train(args: argparse.Namespace) -> int:
    """Workstream 3a: train the sequence world model on windowed states."""
    from training.train import train_world_model

    cfg = _load_config(args.config)
    m, t, w = cfg["model"], cfg["training"], cfg["windowing"]
    train_world_model(
        windows_path=f"{cfg['data']['processed_dir']}/window_state.csv",
        out_dir=t["save_dir"],
        seq_len=w["seq_len"],
        hidden_size=m["hidden_size"],
        num_layers=m["num_layers"],
        dropout=m["dropout"],
        epochs=t["epochs"],
        batch_size=t["batch_size"],
        lr=t["learning_rate"],
        weight_decay=t["weight_decay"],
        val_split=t["val_split"],
        test_split=t["test_split"],
        model_type=m.get("type", "lstm"),
        attack_loss_weight=t.get("attack_loss_weight", 5.0),
        pos_weight=t.get("pos_weight"),
        grad_clip=t.get("grad_clip", 1.0),
        lr_patience=t.get("lr_patience", 8),
        lr_factor=t.get("lr_factor", 0.5),
        early_stop_patience=t.get("early_stop_patience", 15),
    )
    return 0


def run_forecast(args: argparse.Namespace) -> int:
    """Workstream 3b: K-step rollout + infiltration timeline + chart."""
    from training.forecast import run_forecast

    cfg = _load_config(args.config)
    f = cfg["forecasting"]
    run_forecast(
        windows_path=f"{cfg['data']['processed_dir']}/window_state.csv",
        checkpoint=args.snapshot or cfg["training"]["checkpoint"],
        seq_len=cfg["windowing"]["seq_len"],
        k_steps=f["k_steps"],
        threshold=f["threat_threshold"],
        out_dir=cfg["training"]["save_dir"],
    )
    return 0


def run_explain(args: argparse.Namespace) -> int:
    """Workstream 4: attention + SHAP attribution for the forecast."""
    from detection.world_explain import run_explain

    cfg = _load_config(args.config)
    run_explain(
        checkpoint=args.snapshot or cfg["training"]["checkpoint"],
        windows_path=f"{cfg['data']['processed_dir']}/window_state.csv",
        binary_csv=cfg["data"]["binary_csv"],
        seq_len=cfg["windowing"]["seq_len"],
        out_dir=cfg["training"]["save_dir"],
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="CyberForeSight pipeline launcher")
    parser.add_argument(
        "--stage",
        required=True,
        choices=["features", "train", "forecast", "explain", "demo", "benchmark"],
    )
    parser.add_argument("--config", default="configs/world_model.yaml")
    parser.add_argument("--snapshot", default=None)
    parser.add_argument(
        "--csv",
        default=None,
        help="path to a CIC flow CSV to process (default: first CSV in data/raw)",
    )
    parser.add_argument(
        "--window-seconds",
        type=int,
        default=None,
        help="override windowing interval",
    )
    args = parser.parse_args()

    if args.stage == "features":
        return run_features(args)
    if args.stage == "train":
        return run_train(args)
    if args.stage == "forecast":
        return run_forecast(args)
    if args.stage == "explain":
        return run_explain(args)
    if args.stage == "benchmark":
        from detection.benchmark import run_benchmark

        return run_benchmark(args, _load_config(args.config))
    if args.stage == "demo":
        import shutil
        import subprocess
        import time

        root = Path(__file__).resolve().parent
        node = shutil.which("node") or shutil.which("node.exe")
        if not node:
            print("node not found on PATH - start backend and frontend manually", file=sys.stderr)
            return 1

        backend = subprocess.Popen(
            ["node", "server.js"],
            cwd=root / "backend",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        frontend = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=root / "frontend",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("JARVIS backend (Socket.IO :5000) + frontend (Vite :5173) starting...")
        print("Open  http://localhost:5173  and switch to the FORECAST tab")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            backend.terminate()
            frontend.terminate()
        return 0

    print(f"{args.stage}: not yet wired - workstreams 2-6 pending", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())