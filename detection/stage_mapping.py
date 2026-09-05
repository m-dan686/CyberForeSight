"""Workstream 3b - MITRE ATT&CK stage prediction over the world-model forecast.

The world model's predicted NEXT-WINDOW state vector,  S(t+k+1) = f(S(t+k)),
is a behavioural fingerprint of the network "k minutes in the future".  This
module converts that fingerprint into an ATT&CK stage forecast using a small,
interpretable, rule-level scoring model:

    stage score  =  sum( w_f * sigmoid( d_f * z_f / 2 ) )
    stage        =  argmax( stage_score * attack_probability )
    confidence   =  sigmoid( normalized top score ) * attack_probability

where z_f is the robust-scaled deviation of feature f from the benign median
(the state vector is already benign-fit robust-scaled:  0 == benign median,
1 == benign IQR) and d_f is +1 / -1 for "more is suspicious" / "less is
suspicious".  The recurrence across forecast steps gives temporal persistence;
prob_next weights the fingerprint by how likely an intrusion is at all.

This is intentionally a transparent heuristic layer rather than another
black box: every stage maps to a fixed MITRE technique and an explicit signal
set, so the forecast panel can show *why* a stage was chosen.  The heuristic
fingerprints are documented in README (features -> behavioural meaning).

Stages follow the CIC-IDS-2018 Infiltration scenario: Recon -> Initial Access
(public-facing service exploitation) -> Command & Control (beaconing) ->
Exfiltration / Impact, with Lateral Movement retained for generality.
"""

from __future__ import annotations

import numpy as np

STAGES: list[dict[str, object]] = [
    {
        "id": "reconnaissance",
        "stage": "RECONNAISSANCE",
        "technique": "T1046 - Network Service Discovery",
        "tactic": "Discovery",
        "features": {
            "syn_cnt": (+1, 2.0),
            "flow_pkts_p_s": (+1, 1.5),
            "flow_duration": (-1, 1.0),
            "fwd_pkt_len_mean": (-1, 1.0),
            "ack_cnt": (-1, 0.5),
        },
    },
    {
        "id": "initial_access",
        "stage": "INITIAL ACCESS",
        "technique": "T1190 - Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "features": {
            "tot_fwd_pkts": (+1, 1.5),
            "fwd_act_data_pkts": (+1, 1.5),
            "subflow_fwd_pkts": (+1, 1.5),
            "flow_byts_p_s": (+1, 1.0),
            "flow_iat_std": (-1, 0.5),
        },
    },
    {
        "id": "lateral_movement",
        "stage": "LATERAL MOVEMENT",
        "technique": "T1021 - Remote Services",
        "tactic": "Lateral Movement",
        "features": {
            "init_fwd_win": (+1, 1.5),
            "init_bwd_win": (+1, 1.5),
            "pkt_len_std": (+1, 1.0),
            "bwd_pkt_len_mean": (+1, 1.0),
            "tot_bwd_byts": (+1, 0.5),
        },
    },
    {
        "id": "c2",
        "stage": "COMMAND AND CONTROL",
        "technique": "T1071 - Application Layer Protocol",
        "tactic": "Command and Control",
        "features": {
            "ack_cnt": (+1, 2.0),
            "bwd_pkts": (+1, 1.5),
            "flow_iat_std": (-1, 1.0),
            "flow_byts_p_s": (+1, 0.5),
            "pkt_len_std": (-1, 0.5),
        },
    },
    {
        "id": "exfiltration",
        "stage": "EXFILTRATION",
        "technique": "T1030 - Data Transfer Size Limits (bidi asymmetry)",
        "tactic": "Exfiltration",
        "features": {
            "tot_bwd_byts": (+1, 2.0),
            "down_up_ratio": (+1, 1.5),
            "bwd_pkt_len_mean": (+1, 1.0),
            "flow_byts_p_s": (+1, 1.0),
            "tot_bwd_pkts": (+1, 0.5),
        },
    },
    {
        "id": "impact",
        "stage": "IMPACT",
        "technique": "T1498 - Network Denial of Service",
        "tactic": "Impact",
        "features": {
            "syn_cnt": (+1, 2.0),
            "flow_pkts_p_s": (+1, 2.0),
            "rst_cnt": (+1, 1.0),
            "init_fwd_win": (-1, 0.5),
            "flow_byts_p_s": (+1, 0.5),
        },
    },
]

# fallback when the fingerprint does not separate cleanly but the model is
# confident an intrusion is underway (dataset scenario: Infiltration -> backdoor)
_DEFAULT_STAGE = {
    "id": "c2",
    "stage": "COMMAND AND CONTROL",
    "technique": "T1071 - Application Layer Protocol",
    "tactic": "Command and Control",
}


def _act(z: float, direction: int, scale: float = 2.0) -> float:
    """Sigmoid on directional robust-scaled deviation -> [0,1] suspicion."""
    return float(1.0 / (1.0 + np.exp(-direction * z / scale)))


def _feature_index(name: str, z: np.ndarray, feature_names: list[str]) -> float:
    try:
        return float(z[feature_names.index(name)])
    except (ValueError, IndexError):  # feature absent from this dataset variant
        return 0.0


def score_stages(
    state: np.ndarray,
    feature_names: list[str],
    attack_probability: float,
) -> dict[str, object]:
    """Score every stage from one state vector (observed or predicted).

    Returns chosen stage, confidence, per-stage scores and the top signals
    (feature directions that actually contributed).
    """
    z = np.asarray(state, dtype=np.float64).ravel()
    if z.size == 0:
        z = np.zeros(len(feature_names), dtype=np.float64)

    scores: dict[str, float] = {}
    signals: dict[str, list[str]] = {}
    for row in STAGES:
        feats: dict[str, tuple[int, float]] = row["features"]  # type: ignore[assignment]
        total_w = sum(w for _, w in feats.values())
        acc = 0.0
        top: list[tuple[float, str]] = []
        for fname, (direction, w) in feats.items():
            contrib = w * _act(_feature_index(fname, z, feature_names), direction)
            acc += contrib
            top.append((contrib, fname))
        scores[str(row["stage"])] = acc / max(total_w, 1e-9)
        top.sort(reverse=True)
        signals[str(row["stage"])] = [t[1] for t in top[:3]]

    best_stage = max(scores, key=scores.get)
    norm_best = float(scores[best_stage])
    p_attack = float(np.clip(attack_probability, 0.0, 1.0))
    confidence = float(1.0 / (1.0 + np.exp(-(norm_best - 0.35) * 6.0))) * p_attack

    meta = next(
        (r for r in STAGES if r["stage"] == best_stage),
        _DEFAULT_STAGE,  # type: ignore[arg-type]
    )
    if p_attack < 0.4 and norm_best < 0.55:
        meta = _DEFAULT_STAGE
        best_stage = str(_DEFAULT_STAGE["stage"])
        confidence = 0.5 * p_attack

    return {
        "stage": best_stage,
        "stage_id": str(meta["id"]),
        "technique": str(meta["technique"]),
        "tactic": str(meta["tactic"]),
        "confidence": round(confidence, 4),
        "attack_probability": round(p_attack, 4),
        "scores": {k: round(v, 4) for k, v in sorted(scores.items(), key=lambda kv: -kv[1])},
        "top_signals": signals.get(best_stage, []),
    }


def predict_timeline(
    states: np.ndarray,
    feature_names: list[str],
    attack_probs: np.ndarray | None = None,
) -> list[dict[str, object]]:
    """Stage map over an array of states (rows aligned to prob_next)."""
    probs = (
        np.ones(len(states))
        if attack_probs is None or len(attack_probs) != len(states)
        else attack_probs
    )
    return [
        score_stages(row, feature_names, float(p)) for row, p in zip(states, probs)
    ]