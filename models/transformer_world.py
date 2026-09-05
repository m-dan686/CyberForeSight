"""World model — Temporal Transformer variant for SIH-26153.

Same contract as WorldModelLSTM (state head + attack head + attention) so the
forecast / explain / benchmark stages are architecture-agnostic:

    forward(x)            -> (predicted_next_state, attack_logit, attn_weights)
    predict_step(x)       -> predicted_next_state
    attack_probability(x) -> P(attack in the following window)

Design: the window-state sequence S_(t-k)..S_t is projected, position-encoded,
passed through an encoder-only Transformer (self-attention across windows),
pooled with mean-over-time and read out through the two heads.  The attention
weights (mean over heads/layers) expose which historical windows drove the
prediction — the Workstream-4 explainability signal.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


class WorldModelTransformer(nn.Module):
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 96,
        num_layers: int = 2,
        dropout: float = 0.3,
        output_dim: int | None = None,
        nhead: int = 4,
        max_seq: int = 64,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.output_dim = output_dim or input_dim
        self.nhead = nhead

        self.proj = nn.Linear(input_dim, hidden_dim)
        self.pos = nn.Parameter(torch.zeros(1, max_seq, hidden_dim))
        nn.init.normal_(self.pos, std=0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=nhead,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(hidden_dim)
        self.drop = nn.Dropout(dropout)

        self.state_head = nn.Linear(hidden_dim, self.output_dim)
        self.attack_head = nn.Linear(hidden_dim, 1)

    def forward(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]:
        """Returns (predicted_next_state, attack_logit, attention_weights)."""
        b, t, _ = x.shape
        h = self.proj(x) + self.pos[:, :t, :]
        h = self.drop(h)

        attn_blocks: list[torch.Tensor] = []
        for layer in self.encoder.layers:
            attn_out, attn_matrix = layer.self_attn(
                h, h, h, need_weights=True, average_attn_weights=True
            )
            attn_blocks.append(attn_matrix)
            h = layer.norm1(h + layer.dropout1(attn_out))
            ff = layer.linear2(layer.dropout(layer.activation(layer.linear1(h))))
            h = layer.norm2(h + layer.dropout2(ff))

        h = self.norm(h)
        context = h.mean(dim=1)

        state_pred = self.state_head(context)
        attack_logit = self.attack_head(context)
        if attn_blocks:
            attn = torch.stack(attn_blocks).mean(dim=0).mean(dim=1)
        else:
            attn = None
        return state_pred, attack_logit, attn

    def predict_step(self, x: torch.Tensor) -> torch.Tensor:
        state_pred, _, _ = self(x)
        return state_pred

    def attack_probability(self, x: torch.Tensor) -> torch.Tensor:
        _, logit, _ = self(x)
        return torch.sigmoid(logit)