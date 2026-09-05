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


def main() -> int:
    parser = argparse.ArgumentParser(description="CyberForeSight pipeline launcher")
    parser.add_argument(
        "--stage",
        required=True,
        choices=["features", "train", "forecast", "explain", "demo", "benchmark"],
    )
    parser.add_argument("--config", default="configs/world_model.yaml")
    parser.add_argument("--snapshot", default=None)
    args = parser.parse_args()

    if args.stage == "demo":
        import os
        import subprocess

        return subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "dashboard/app.py",
                "--server.port",
                "8501",
            ],
            env={**os.environ, "PYTHONPATH": os.getcwd()},
        )

    print(f"{args.stage}: not yet wired - workstreams 2-6 pending", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())