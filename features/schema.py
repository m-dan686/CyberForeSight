"""Canonical flow schema and CIC-IDS label/follow normalization.

The CIC family (2017 and 2018) publishes flow CSVs with slightly different
column names for the same underlying CICFlowMeter features.  extract_flow.py
maps any of those variants onto a single canonical lowercase schema so the
rest of the pipeline (windowing, training, forecasting) never needs to know
which dataset variant produced the rows.
"""

from __future__ import annotations

import re
from typing import Any

# Canonical schema: lowercase snake_case, ordered.  The world-model state
# vector is built from the numeric subset of these columns only.
CANONICAL_FEATURES: list[str] = [
    "dst_port",
    "protocol",
    "timestamp",
    "flow_duration",
    "tot_fwd_pkts",
    "tot_bwd_pkts",
    "tot_fwd_byts",
    "tot_bwd_byts",
    "fwd_pkt_len_mean",
    "fwd_pkt_len_std",
    "bwd_pkt_len_mean",
    "bwd_pkt_len_std",
    "flow_byts_p_s",
    "flow_pkts_p_s",
    "flow_iat_mean",
    "flow_iat_std",
    "flow_iat_max",
    "flow_iat_min",
    "fwd_iat_mean",
    "fwd_iat_std",
    "fwd_iat_max",
    "fwd_iat_min",
    "bwd_iat_mean",
    "bwd_iat_std",
    "bwd_iat_max",
    "bwd_iat_min",
    "fwd_hdr_len",
    "bwd_hdr_len",
    "pkt_len_min",
    "pkt_len_max",
    "pkt_len_mean",
    "pkt_len_std",
    "syn_cnt",
    "ack_cnt",
    "fin_cnt",
    "rst_cnt",
    "psh_cnt",
    "urg_cnt",
    "down_up_ratio",
    "init_fwd_win",
    "init_bwd_win",
    "fwd_act_data_pkts",
    "fwd_seg_size_min",
    "subflow_fwd_pkts",
    "subflow_bwd_pkts",
    "label",
]

# Numeric features that participate in the state vector S_t.
STATE_FEATURES: list[str] = [
    "flow_duration",
    "tot_fwd_pkts",
    "tot_bwd_pkts",
    "tot_fwd_byts",
    "tot_bwd_byts",
    "fwd_pkt_len_mean",
    "fwd_pkt_len_std",
    "bwd_pkt_len_mean",
    "bwd_pkt_len_std",
    "flow_byts_p_s",
    "flow_pkts_p_s",
    "flow_iat_mean",
    "flow_iat_std",
    "flow_iat_max",
    "flow_iat_min",
    "fwd_iat_mean",
    "fwd_iat_std",
    "fwd_iat_max",
    "fwd_iat_min",
    "bwd_iat_mean",
    "bwd_iat_std",
    "bwd_iat_max",
    "bwd_iat_min",
    "fwd_hdr_len",
    "bwd_hdr_len",
    "pkt_len_min",
    "pkt_len_max",
    "pkt_len_mean",
    "pkt_len_std",
    "syn_cnt",
    "ack_cnt",
    "fin_cnt",
    "rst_cnt",
    "psh_cnt",
    "urg_cnt",
    "down_up_ratio",
    "init_fwd_win",
    "init_bwd_win",
    "fwd_act_data_pkts",
    "fwd_seg_size_min",
    "subflow_fwd_pkts",
    "subflow_bwd_pkts",
]

# All known source column aliases -> canonical name.  New CIC-IDS variants
# can be added here without touching the downstream pipeline.
FLOW_ALIAS: dict[str, tuple[str, ...]] = {
    "dst_port": ("Dst Port", "Destination Port", "Destination Port "),
    "protocol": ("Protocol",),
    "timestamp": ("Timestamp",),
    "flow_duration": ("Flow Duration", "Flow Duration "),
    "tot_fwd_pkts": ("Tot Fwd Pkts", "Total Fwd Packets", "Fwd Pkts"),
    "tot_bwd_pkts": ("Tot Bwd Pkts", "Total Backward Packets", "Bwd Pkts"),
    "tot_fwd_byts": ("TotLen Fwd Pkts", "Total Length of Fwd Packets", "Total Len Fwd Packets"),
    "tot_bwd_byts": ("TotLen Bwd Pkts", "Total Length of Bwd Packets", "Total Len Bwd Packets"),
    "fwd_pkt_len_mean": ("Fwd Pkt Len Mean", "Fwd Packet Length Mean", "Fwd Packet Length Mean "),
    "fwd_pkt_len_std": ("Fwd Pkt Len Std", "Fwd Packet Length Std"),
    "bwd_pkt_len_mean": ("Bwd Pkt Len Mean", "Bwd Packet Length Mean"),
    "bwd_pkt_len_std": ("Bwd Pkt Len Std", "Bwd Packet Length Std"),
    "flow_byts_p_s": ("Flow Byts/s", "Flow Bytes/s", "Flow Bytes/s "),
    "flow_pkts_p_s": ("Flow Pkts/s", "Flow Packets/s"),
    "flow_iat_mean": ("Flow IAT Mean", "Flow IAT Mean "),
    "flow_iat_std": ("Flow IAT Std",),
    "flow_iat_max": ("Flow IAT Max", "Flow IAT Max "),
    "flow_iat_min": ("Flow IAT Min",),
    "fwd_iat_mean": ("Fwd IAT Mean", "Fwd IAT Mean "),
    "fwd_iat_std": ("Fwd IAT Std",),
    "fwd_iat_max": ("Fwd IAT Max", "Fwd IAT Max "),
    "fwd_iat_min": ("Fwd IAT Min",),
    "bwd_iat_mean": ("Bwd IAT Mean", "Bwd IAT Mean "),
    "bwd_iat_std": ("Bwd IAT Std",),
    "bwd_iat_max": ("Bwd IAT Max", "Bwd IAT Max "),
    "bwd_iat_min": ("Bwd IAT Min",),
    "fwd_hdr_len": ("Fwd Header Len", "Fwd Header Length"),
    "bwd_hdr_len": ("Bwd Header Len", "Bwd Header Length"),
    "pkt_len_min": ("Pkt Len Min", "Min Packet Length"),
    "pkt_len_max": ("Pkt Len Max", "Max Packet Length"),
    "pkt_len_mean": ("Pkt Len Mean", "Average Packet Size"),
    "pkt_len_std": ("Pkt Len Std", "Packet Length Std"),
    "syn_cnt": ("SYN Flag Cnt", "SYN Flag Count"),
    "ack_cnt": ("ACK Flag Cnt", "ACK Flag Count"),
    "fin_cnt": ("FIN Flag Cnt", "FIN Flag Count"),
    "rst_cnt": ("RST Flag Cnt", "RST Flag Count"),
    "psh_cnt": ("PSH Flag Cnt", "PSH Flag Count"),
    "urg_cnt": ("URG Flag Cnt", "URG Flag Count"),
    "down_up_ratio": ("Down/Up Ratio",),
    "init_fwd_win": ("Init Fwd Win Byts", "Init_Win_bytes_forward"),
    "init_bwd_win": ("Init Bwd Win Byts", "Init_Win_bytes_backward"),
    "fwd_act_data_pkts": ("Fwd Act Data Pkts", "act_data_pkt_fwd"),
    "fwd_seg_size_min": ("Fwd Seg Size Min",),
    "subflow_fwd_pkts": ("Subflow Fwd Pkts",),
    "subflow_fwd_byts": ("Subflow Fwd Byts",),
    "subflow_bwd_pkts": ("Subflow Bwd Pkts",),
    "subflow_bwd_byts": ("Subflow Bwd Byts",),
    "label": ("Label",),
}

# Substrings that mark a row as benign regardless of case/whitespace.
BENIGN_HINTS: tuple[str, ...] = ("benign", "normal")

# Canonical attack-progression class map (raw CIC label -> MITRE-friendly class).
_CLASS_MAP: list[tuple[str, str]] = [
    ("infilteration", "Infiltration"),
    ("infiltration", "Infiltration"),
    ("sshpatator", "BruteForce"),
    ("ftppatator", "BruteForce"),
    ("brute force", "BruteForce"),
    ("bruteforce", "BruteForce"),
    ("dos attacks-hulk", "DoS"),
    ("goldeneye", "DoS"),
    ("slowloris", "DoS"),
    ("slowhttptest", "DoS"),
    ("slowloris2", "DoS"),
    ("httpflood", "DoS"),
    ("dos", "DoS"),
    ("ddos", "DDoS"),
    ("loic", "DDoS"),
    ("bots", "Botnet"),
    ("botnet", "Botnet"),
    ("heartbleed", "Heartbleed"),
    ("portscan", "PortScan"),
    ("sqli", "WebAttack"),
    ("sql injection", "WebAttack"),
    ("xss", "WebAttack"),
    ("web attack", "WebAttack"),
    ("web attacks", "WebAttack"),
    ("ddos attack", "DDoS"),
    ("benign", "Benign"),
]


def canonical_label(raw: Any) -> str:
    """Strip CIC formatting noise ('PR-ADDR-BENIGN.' etc.) to attack class."""
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s).strip(" .\t\r\n")
    low = s.lower()
    if any(h in low for h in BENIGN_HINTS) and "attack" not in low:
        return "Benign"
    for needle, cls in _CLASS_MAP:
        if needle in low:
            return cls
    return s if s.lower() != s else s


def is_benign_label(label: str) -> bool:
    return canonical_label(label) == "Benign"


def attack_class(label: str) -> int:
    """Binary outcome used by the classifier head and binary dataset."""
    return 0 if is_benign_label(label) else 1