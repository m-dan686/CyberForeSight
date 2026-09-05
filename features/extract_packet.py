"""Packet-level feature extraction from a PCAP (optional; Scapy).

Runs only when raw capture files are supplied in addition to the CIC flow CSVs.
Produces per-window packet statistics aligned to the same 60 s grid used by
features/window.py, complementing the flow-level state vector with:

  ttl_mean / ttl_std            - hop-distance fingerprint (recon / exfil paths)
  tcp_win_mean / tcp_win_std    - receive-window envelope (slowloris sees dips)
  payload_byts_mean / sum       - data carried per window
  ip_frag_cnt                   - fragmented datagrams (covert exfil / floods)
  tcp_pshack_cnt                - data-carrying PSH+ACK exchanges (C2 chatter)
  distinct_src/dst_ports        - port-scan diversity per window
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    import scapy.all as sp
except ImportError:  # pragma: no cover - scapy optional
    sp = None


PACKET_STATE_FEATURES = [
    "ttl_mean",
    "ttl_std",
    "tcp_win_mean",
    "tcp_win_std",
    "payload_byts_mean",
    "payload_byts_sum",
    "ip_frag_cnt",
    "tcp_pshack_cnt",
    "distinct_src_ports",
    "distinct_dst_ports",
]


def extract_packet_pcap(pcap_path: str | Path, window_seconds: int = 60) -> pd.DataFrame:
    """Read a PCAP and aggregate packet statistics into windowed rows."""
    if sp is None:
        raise ImportError("scapy is not installed - run: .venv/Scripts/pip install scapy")

    recs: list[dict[str, float]] = []
    for pkt in sp.PcapReader(str(pcap_path)):
        recs.append({
            "ts": float(pkt.time),
            "ttl": _ttl_of(pkt),
            "tcp_win": _tcp_window(pkt),
            "payload": _payload_byts(pkt),
            "frag": _fragmented(pkt),
            "pshack": _pshack(pkt),
            "srcp": _ports(pkt)[0],
            "dstp": _ports(pkt)[1],
        })

    if not recs:
        return pd.DataFrame(columns=PACKET_STATE_FEATURES)

    df = pd.DataFrame(recs)
    df["window_start"] = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_localize(None).dt.floor(
        f"{window_seconds}s"
    )

    g = df.groupby("window_start")
    out = pd.DataFrame({
        "ttl_mean": g["ttl"].mean(),
        "ttl_std": g["ttl"].std().fillna(0.0),
        "tcp_win_mean": g["tcp_win"].mean(),
        "tcp_win_std": g["tcp_win"].std().fillna(0.0),
        "payload_byts_mean": g["payload"].mean(),
        "payload_byts_sum": g["payload"].sum(),
        "ip_frag_cnt": g["frag"].sum(),
        "tcp_pshack_cnt": g["pshack"].sum(),
        "distinct_src_ports": g["srcp"].nunique(),
        "distinct_dst_ports": g["dstp"].nunique(),
    }).reset_index()
    return out[["window_start", *PACKET_STATE_FEATURES]]


def _ttl_of(pkt: object) -> float:
    if sp is None:
        return 64.0
    ip = pkt.getlayer(sp.IP) if pkt is not None else None
    if ip is None:
        ip6 = pkt.getlayer(sp.IPv6)
        return float(getattr(ip6, "hlim", 64.0)) if ip6 is not None else 64.0
    return float(getattr(ip, "ttl", 64.0))


def _tcp_window(pkt: object) -> float:
    if sp is None:
        return 0.0
    tcp = pkt.getlayer(sp.TCP) if pkt is not None else None
    return float(getattr(tcp, "window", 0) or 0) if tcp is not None else 0.0


def _payload_byts(pkt: object) -> float:
    if sp is None:
        return 0.0
    raw = pkt.getlayer(sp.Raw) if pkt is not None else None
    return float(len(bytes(raw))) if raw is not None else 0.0


def _fragmented(pkt: object) -> float:
    if sp is None:
        return 0.0
    ip = pkt.getlayer(sp.IP) if pkt is not None else None
    if ip is None:
        return 0.0
    frag = getattr(ip, "frag", 0) or 0
    flags = getattr(ip, "flags", 0) or 0
    return float(int(flags & 1) or int(frag) > 0)


def _pshack(pkt: object) -> float:
    if sp is None:
        return 0.0
    tcp = pkt.getlayer(sp.TCP) if pkt is not None else None
    if tcp is None:
        return 0.0
    flags = getattr(tcp, "flags", 0) or 0
    return float(int(flags & 0x28) == 0x28)


def _ports(pkt: object) -> tuple[float, float]:
    if sp is None:
        return 0.0, 0.0
    layer = None
    if pkt is not None:
        layer = pkt.getlayer(sp.TCP) or pkt.getlayer(sp.UDP)
    if layer is None:
        return 0.0, 0.0
    return float(getattr(layer, "sport", 0) or 0), float(getattr(layer, "dport", 0) or 0)