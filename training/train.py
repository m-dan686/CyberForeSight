"""World model training: sequence windows -> next-state regression + attack head.

Reads data/processed/window_state.csv (already robust-scaled), builds
S_(t-k)..S_t -> S_t+1 sequences, splits chronologically by window index
(train / val / test) so no future traffic leaks into the past, trains the
WorldModelLSTM with an MSE state loss + BCE attack loss, saves the checkpoint,
loss curve, and edge metrics to models/.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn, optim

from models.lstm_world import WorldModelLSTM


class SequenceBuilder:
    """Turns a window state frame into (X, y_state, y_attack) sequences."""

    def __init__(self, seq_len: int = 10) -> None:
        self.seq_len = seq_len

    def build(self, windows: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        states = np.stack(
            [windows[c].to_numpy(float) for c in windows.columns if c.startswith("state_")],
            axis=1,
        )
        attack = windows["attack"].to_numpy(int)
        starts = windows["window_start"].to_numpy()
        seq, y_state, y_attack, idx = [], [], [], []
        n = states.shape[0]
        for i in range(self.seq_len - 1, n - 1):
            seq.append(states[i - self.seq_len + 1 : i + 1])
            y_state.append(states[i + 1])
            y_attack.append(attack[i + 1])
            idx.append(i + 1)
        return (
            np.asarray(seq, dtype=np.float32),
            np.asarray(y_state, dtype=np.float32),
            np.asarray(y_attack, dtype=np.float32),
            np.asarray(idx, dtype=np.int64),
        )


def split_sequences(
    seq: np.ndarray,
    y_state: np.ndarray,
    y_attack: np.ndarray,
    idx: np.ndarray,
    n_total: int,
    val_split: float,
    test_split: float,
) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
    """Chronological split in target-window space (no temporal leakage)."""
    n_seq = seq.shape[0]
    split_val = int(n_total * (1 - val_split - test_split))
    split_test = int(n_total * (1 - test_split))
    parts: dict[str, list[np.ndarray]] = {
        "train": [], "val": [], "test": [],
    }
    for mask_lo, mask_hi, name in [
        (0, split_val, "train"),
        (split_val, split_test, "val"),
        (split_test, n_total, "test"),
    ]:
        m = (idx >= mask_lo) & (idx < mask_hi)
        parts[name] = [
            seq[m], y_state[m], y_attack[m], idx[m],
        ]
    return parts


class Trainer:
    def __init__(
        self,
        model: nn.Module,
        device: torch.device,
        lr: float = 1e-3,
        weight_decay: float = 1e-5,
    ) -> None:
        self.model = model.to(device)
        self.device = device
        self.state_loss = nn.MSELoss()
        self.attack_loss = nn.BCEWithLogitsLoss()
        self.optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    def _to_tensor(self, arr: np.ndarray) -> torch.Tensor:
        return torch.from_numpy(arr).to(self.device)

    def fit(
        self,
        train: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
        val: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
        epochs: int,
        batch_size: int,
    ) -> list[float]:
        xs, ys, ya, _ = train
        vx, vy, vya, _ = val
        xs_t, ys_t, ya_t = (
            self._to_tensor(xs), self._to_tensor(ys), self._to_tensor(ya),
        )
        vx_t, vy_t, vya_t = (
            self._to_tensor(vx), self._to_tensor(vy), self._to_tensor(vya),
        )
        n = xs_t.shape[0]
        history: list[float] = []
        for epoch in range(1, epochs + 1):
            self.model.train()
            perm = torch.randperm(n, device=self.device)
            total_loss = 0.0
            n_batches = 0
            for start in range(0, n, batch_size):
                batch = perm[start : start + batch_size]
                pred, logit, _ = self.model(xs_t[batch])
                loss = self.state_loss(pred, ys_t[batch]) + self.attack_loss(
                    logit.squeeze(-1), ya_t[batch]
                )
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                total_loss += float(loss.item())
                n_batches += 1

            self.model.eval()
            with torch.no_grad():
                vpred, vlogit, _ = self.model(vx_t)
                v_loss = float(self.state_loss(vpred, vy_t)) + float(
                    self.attack_loss(vlogit.squeeze(-1), vya_t)
                )
            history.append(float(total_loss / max(n_batches, 1)))
            if epoch == 1 or epoch % 5 == 0 or epoch == epochs:
                print(f"    epoch {epoch:3d}/{epochs}  train {history[-1]:.4f}  val {v_loss:.4f}")
        return history

    def evaluate(
        self, data: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    ) -> dict[str, float]:
        xs, ys, ya, _ = data
        self.model.eval()
        with torch.no_grad():
            pred, logit, _ = self.model(self._to_tensor(xs))
        ys_t, ya_t = self._to_tensor(ys), self._to_tensor(ya)
        mse = float(self.state_loss(pred, ys_t).item())
        prob = torch.sigmoid(logit.squeeze(-1)).cpu().numpy()
        ya_np = ya_t.cpu().numpy()
        return {
            "next_state_mse": float(mse),
            "attack_accuracy": float(((prob > 0.5).astype(int) == ya_np).mean()),
            "attack_fpr": float(((prob > 0.5) & (ya_np == 0)).sum() / max((ya_np == 0).sum(), 1)),
            "known_positives": int(ya_np.sum()),
        }


def train_world_model(
    windows_path: str | Path,
    out_dir: str | Path,
    seq_len: int,
    hidden_size: int,
    num_layers: int,
    dropout: float,
    epochs: int,
    batch_size: int,
    lr: float,
    weight_decay: float,
    val_split: float,
    test_split: float,
    device: torch.device | None = None,
) -> dict[str, object]:
    windows = pd.read_csv(windows_path)
    device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(42)

    builder = SequenceBuilder(seq_len)
    seq, y_state, y_attack, idx = builder.build(windows)
    n_seq = seq.shape[0]
    n_total = windows.shape[0]
    parts = split_sequences(seq, y_state, y_attack, idx, n_total, val_split, test_split)

    model = WorldModelLSTM(
        input_dim=seq.shape[2], hidden_dim=hidden_size,
        num_layers=num_layers, dropout=dropout,
    )
    trainer = Trainer(model, device, lr=lr, weight_decay=weight_decay)
    print(f"[train] device={device} sequences={n_seq} "
          f"train={len(parts['train'][0])} val={len(parts['val'][0])} test={len(parts['test'][0])} "
          f"state_dim={seq.shape[2]}")

    history = trainer.fit(parts["train"], parts["val"], epochs=epochs, batch_size=batch_size)

    train_metrics = trainer.evaluate(parts["train"])
    val_metrics = trainer.evaluate(parts["val"])
    test_metrics = trainer.evaluate(parts["test"])

    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "config": {
                "input_dim": seq.shape[2],
                "hidden_size": hidden_size,
                "num_layers": num_layers,
                "dropout": dropout,
                "seq_len": seq_len,
            },
            "scaler_features": [c for c in windows.columns if c.startswith("state_")],
        },
        out_dir_p / "world_model_lstm.pt",
    )
    (out_dir_p / "training_history.json").write_text(
        json.dumps(history, indent=2)
    )
    (out_dir_p / "train_metrics.json").write_text(
        json.dumps(
            {
                "train": train_metrics,
                "val": val_metrics,
                "test": test_metrics,
                "n_train": len(parts["train"][0]),
                "n_val": len(parts["val"][0]),
                "n_test": len(parts["test"][0]),
            },
            indent=2,
        )
    )
    print(f"[train] metrics -> {out_dir_p / 'train_metrics.json'}")
    print(f"[train] checkpoint -> {out_dir_p / 'world_model_lstm.pt'}")
    return {"train": train_metrics, "val": val_metrics, "test": test_metrics}