"""World model training: sequence windows -> next-state regression + attack head.

Reads data/processed/window_state.csv (already robust-scaled), builds
S_(t-k)..S_t -> S_t+1 sequences, splits chronologically by window index
(train / val / test) so no future traffic leaks into the past, trains the
sequence model (WorldModelLSTM or WorldModelTransformer) with an MSE state
loss + a class-weighted BCE attack loss, then saves the checkpoint, the
val-tuned detection threshold, loss curves, and edge metrics to models/.

Balance / convergence notes (SIH-26153 6.x):
  * The timeline is ~3.7:1 benign:attack (570 windows / 155 attack); the
    attack head is weighted with pos_weight = #benign/#attack so it does not
    collapse to "always benign".
  * attack_loss_weight scales the BCE term relative to the state MSE, whose
    magnitude would otherwise dominate the joint objective.
  * Learning rate is reduced on a val-loss plateau; training stops early and
    restores the best (lowest val-loss) weights, preventing overfit on the
    ~795 sequence examples.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn, optim

from models.lstm_world import WorldModelLSTM
from models.transformer_world import WorldModelTransformer


def best_threshold(y: np.ndarray, prob: np.ndarray) -> tuple[float, float]:
    """Threshold in [0.05, 0.95] maximising F1 (tie -> higher threshold)."""
    y = np.asarray(y).astype(int)
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
    return best_t, best_f1


def build_model(model_type: str, input_dim: int, hidden_size: int,
                num_layers: int, dropout: float) -> nn.Module:
    if model_type == "transformer":
        return WorldModelTransformer(
            input_dim=input_dim, hidden_dim=hidden_size,
            num_layers=num_layers, dropout=dropout,
        )
    return WorldModelLSTM(
        input_dim=input_dim, hidden_dim=hidden_size,
        num_layers=num_layers, dropout=dropout,
    )


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
    parts: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = {}
    for mask_lo, mask_hi, name in [
        (0, split_val, "train"),
        (split_val, split_test, "val"),
        (split_test, n_total, "test"),
    ]:
        m = (idx >= mask_lo) & (idx < mask_hi)
        parts[name] = (
            seq[m], y_state[m], y_attack[m], idx[m],
        )
    return parts


class Trainer:
    def __init__(
        self,
        model: nn.Module,
        device: torch.device,
        lr: float = 1e-3,
        weight_decay: float = 1e-3,
        attack_weight: float = 5.0,
        pos_weight: float | None = None,
    ) -> None:
        self.model = model.to(device)
        self.device = device
        self.state_loss = nn.MSELoss()
        pw = torch.tensor([pos_weight], dtype=torch.float32, device=device) if pos_weight else None
        self.attack_loss = (
            nn.BCEWithLogitsLoss(pos_weight=pw) if pw is not None else nn.BCEWithLogitsLoss()
        )
        self.attack_weight = attack_weight
        self.optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

    def _to_tensor(self, arr: np.ndarray) -> torch.Tensor:
        return torch.from_numpy(arr).to(self.device)

    def _joint_loss(self, state_pred: torch.Tensor, state_y: torch.Tensor,
                    logit: torch.Tensor, attack_y: torch.Tensor) -> torch.Tensor:
        return self.state_loss(state_pred, state_y) + self.attack_weight * self.attack_loss(
            logit.squeeze(-1), attack_y
        )

    def fit(
        self,
        train: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
        val: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray],
        epochs: int,
        batch_size: int,
        grad_clip: float = 1.0,
        lr_patience: int = 8,
        lr_factor: float = 0.5,
        early_stop_patience: int = 15,
    ) -> tuple[list[float], int]:
        xs, ys, ya, _ = train
        vx, vy, vya, _ = val
        xs_t, ys_t, ya_t = (
            self._to_tensor(xs), self._to_tensor(ys), self._to_tensor(ya),
        )
        vx_t, vy_t, vya_t = (
            self._to_tensor(vx), self._to_tensor(vy), self._to_tensor(vya),
        )
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", factor=lr_factor,
            patience=lr_patience,
        )
        n = xs_t.shape[0]
        history: list[float] = []
        best_val, best_state, best_epoch, stale = float("inf"), None, 0, 0

        for epoch in range(1, epochs + 1):
            self.model.train()
            perm = torch.randperm(n, device=self.device)
            total_loss = 0.0
            n_batches = 0
            for start in range(0, n, batch_size):
                batch = perm[start : start + batch_size]
                pred, logit, _ = self.model(xs_t[batch])
                loss = self._joint_loss(pred, ys_t[batch], logit, ya_t[batch])
                self.optimizer.zero_grad()
                loss.backward()
                if grad_clip:
                    nn.utils.clip_grad_norm_(self.model.parameters(), grad_clip)
                self.optimizer.step()
                total_loss += float(loss.item())
                n_batches += 1

            self.model.eval()
            with torch.no_grad():
                vpred, vlogit, _ = self.model(vx_t)
                v_loss = float(self._joint_loss(vpred, vy_t, vlogit, vya_t))
            history.append(float(total_loss / max(n_batches, 1)))
            scheduler.step(v_loss)

            if v_loss < best_val:
                best_val, best_state, best_epoch, stale = v_loss, {
                    k: v.detach().clone() for k, v in self.model.state_dict().items()
                }, epoch, 0
            else:
                stale += 1

            if epoch == 1 or epoch % 10 == 0 or epoch == epochs:
                print(f"    epoch {epoch:3d}/{epochs}  train {history[-1]:.4f}  "
                      f"val {v_loss:.4f}  lr {self.optimizer.param_groups[0]['lr']:.1e}")

            if stale >= early_stop_patience:
                print(f"    early stop at epoch {epoch} (no val improvement "
                      f"for {early_stop_patience}) - restoring epoch {best_epoch}")
                break

        if best_state is not None:
            self.model.load_state_dict(best_state)
        return history, best_epoch

    def evaluate(
        self, data: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
    ) -> tuple[dict[str, float], np.ndarray]:
        xs, ys, ya, _ = data
        self.model.eval()
        with torch.no_grad():
            pred, logit, _ = self.model(self._to_tensor(xs))
        ys_t, ya_t = self._to_tensor(ys), self._to_tensor(ya)
        mse = float(self.state_loss(pred, ys_t).item())
        prob = torch.sigmoid(logit.squeeze(-1)).cpu().numpy()
        ya_np = ya_t.cpu().numpy()
        auc = float(np.nan)
        if ya_np.sum() and (ya_np == 0).sum():
            from sklearn.metrics import roc_auc_score
            auc = float(roc_auc_score(ya_np, prob))
        metrics = {
            "next_state_mse": round(mse, 6),
            "attack_auc": round(auc, 4) if auc == auc else None,
            "known_positives": int(ya_np.sum()),
            "n": int(len(ya_np)),
        }
        return metrics, prob


def _classify_summary(y: np.ndarray, prob: np.ndarray, threshold: float) -> dict[str, float]:
    pred = (prob >= threshold).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    return {
        "threshold": round(float(threshold), 3),
        "accuracy": round(float((pred == y).mean()), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "fpr": round(float(fp / max((y == 0).sum(), 1)), 4),
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
    model_type: str = "lstm",
    attack_loss_weight: float = 5.0,
    pos_weight: float | None = None,
    grad_clip: float = 1.0,
    lr_patience: int = 8,
    lr_factor: float = 0.5,
    early_stop_patience: int = 15,
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

    if pos_weight is None:
        n_pos = max(int(parts["train"][2].sum()), 1)
        n_neg = max(len(parts["train"][2]) - n_pos, 1)
        pos_weight = n_neg / n_pos
    print(f"[train] pos_weight (attack head) = {pos_weight:.2f}")

    model = build_model(model_type, input_dim=seq.shape[2], hidden_size=hidden_size,
                        num_layers=num_layers, dropout=dropout)
    trainer = Trainer(model, device, lr=lr, weight_decay=weight_decay,
                      attack_weight=attack_loss_weight, pos_weight=pos_weight)
    print(f"[train] model={model_type} device={device} sequences={n_seq} "
          f"train={len(parts['train'][0])} val={len(parts['val'][0])} test={len(parts['test'][0])} "
          f"state_dim={seq.shape[2]}")

    history, best_epoch = trainer.fit(
        parts["train"], parts["val"], epochs=epochs, batch_size=batch_size,
        grad_clip=grad_clip, lr_patience=lr_patience, lr_factor=lr_factor,
        early_stop_patience=early_stop_patience,
    )

    train_metrics, train_prob = trainer.evaluate(parts["train"])
    val_metrics, val_prob = trainer.evaluate(parts["val"])
    test_metrics, test_prob = trainer.evaluate(parts["test"])

    val_t, _ = best_threshold(parts["val"][2], val_prob)
    val_metrics.update(_classify_summary(parts["val"][2], val_prob, val_t))
    train_metrics.update(_classify_summary(parts["train"][2], train_prob, val_t))
    test_metrics.update(_classify_summary(parts["test"][2], test_prob, val_t))

    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    checkpoint_path = out_dir_p / f"world_model_{model_type}.pt"
    torch.save(
        {
            "state_dict": model.state_dict(),
            "config": {
                "model_type": model_type,
                "input_dim": seq.shape[2],
                "hidden_size": hidden_size,
                "num_layers": num_layers,
                "dropout": dropout,
                "seq_len": seq_len,
            },
            "detection_threshold": float(val_t),
            "scaler_features": [c for c in windows.columns if c.startswith("state_")],
        },
        checkpoint_path,
    )
    (out_dir_p / "training_history.json").write_text(
        json.dumps({"loss": history, "best_epoch": best_epoch}, indent=2)
    )
    (out_dir_p / "train_metrics.json").write_text(
        json.dumps(
            {
                "model_type": model_type,
                "val_threshold": float(val_t),
                "pos_weight": float(pos_weight),
                "attack_loss_weight": float(attack_loss_weight),
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
    print(f"[train] val threshold (max F1) = {val_t:.2f}")
    print(f"[train] test  acc={test_metrics['accuracy']} f1={test_metrics['f1']} "
          f"recall={test_metrics['recall']} fpr={test_metrics['fpr']} auc={test_metrics.get('attack_auc')}")
    print(f"[train] metrics -> {out_dir_p / 'train_metrics.json'}")
    print(f"[train] checkpoint -> {checkpoint_path}")
    return {"train": train_metrics, "val": val_metrics, "test": test_metrics}