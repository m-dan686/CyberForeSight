"""World model for SIH-26153: learns P(S_t+1 | S_t) from windowed traffic.

Architecture (per ARCHITECTURE.md section 3):
  LSTM encoder over a sequence of window states S_(t-k)..S_t,
  additive attention over the LSTM hidden states,
  a linear state head predicting the next state S_t+1 (regression, MSE),
  a linear attack head giving the next-window infiltration probability (BCE).

The attention weights expose which historical windows most influenced the
prediction (used by Workstream 4 attribution).
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class WorldModelLSTM(nn.Module):
    """Temporal world model with an attention-readout state + attack head."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
        dropout_p: float = 0.0,
        output_dim: int | None = None,
        attention: bool = True,
    ) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.output_dim = output_dim or input_dim
        self.attention = attention

        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.drop = nn.Dropout(dropout_p or dropout)

        if attention:
            self.att_proj = nn.Linear(hidden_dim, hidden_dim)
            self.att_context = nn.Parameter(torch.zeros(hidden_dim))

        self.state_head = nn.Linear(hidden_dim, self.output_dim)
        self.attack_head = nn.Linear(hidden_dim, 1)

    def forward(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]:
        """Returns (predicted_next_state, attack_logit, attention_weights)."""
        lstm_out, _ = self.lstm(x)
        h = self.drop(lstm_out)

        if self.attention:
            scores = torch.tanh(self.att_proj(h))
            scores = torch.einsum("btl,l->bt", scores, self.att_context)
            attn = F.softmax(scores, dim=1)
            context = torch.einsum("btl,bt->bl", h, attn)
        else:
            attn = None
            context = h[:, -1]

        state_pred = self.state_head(context)
        attack_logit = self.attack_head(context)
        return state_pred, attack_logit, attn

    def predict_step(self, x: torch.Tensor) -> torch.Tensor:
        """Next-state regression output for one autoregressive step."""
        state_pred, _, _ = self(x)
        return state_pred

    def attack_probability(self, x: torch.Tensor) -> torch.Tensor:
        """Sigmoid probability of an attack in the FOLLOWING window."""
        _, logit, _ = self(x)
        return torch.sigmoid(logit)