"""CyberForeSight feature extraction package (Workstream 2).

Flow-level and packet-level feature pipelines that transform raw CIC-IDS
captures into time-windowed network states S_t and ground-truth S_t -> S_t+1
transitions for the world model.
"""

from .schema import (
    BENIGN_HINTS,
    CANONICAL_FEATURES,
    STATE_FEATURES,
    FLOW_ALIAS,
    attack_class,
    canonical_label,
    is_benign_label,
)

__all__ = [
    "BENIGN_HINTS",
    "CANONICAL_FEATURES",
    "STATE_FEATURES",
    "FLOW_ALIAS",
    "attack_class",
    "canonical_label",
    "is_benign_label",
]