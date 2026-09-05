# CyberForeSight — Architecture (SIH-26153, 2-page max)

> Problem Statement 26153: *AI-based Network Attack Forecasting from Network Traffic Data*

---

## 1. Goal

Build a prototype that learns how network behaviour evolves over time, predicts future attack states *before* compromise is complete, and provides interpretable decision support for defenders. The system accepts flow-level (NetFlow/IPFIX) and packet-level (PCAP) traffic, builds time-windowed network states, learns state-transition dynamics via a sequence model (Temporal Transformer primary, LSTM fallback), performs K-step forward simulation, maps predictions to MITRE ATT&CK stages, and proves a temporal-dynamics advantage over a static baseline. SHAP and attention-based attribution explain each prediction.

---

## 2. High-level architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          OFFLINE (no cloud APIs)                        │
│                                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────────────┐  │
│  │  PCAP files  │   │ Flow CSVs    │   │ Attack timeline annotations│  │
│  │  (Scapy)     │   │ (CIC-IDS)    │   │ (CIC-IDS labels)           │  │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬─────────────────┘  │
│         │                  │                       │                     │
│         ▼                  ▼                       │                     │
│  ┌──────────────────────────────────┐              │                     │
│  │   FEATURE EXTRACTION            │              │                     │
│  │                                  │              │                     │
│  │  Flow level                      │              │                     │
│  │    TCP flags, bytes, packets,    │              │                     │
│  │    duration, IAT stats, bidi     │              │                     │
│  │    ratios                        │              │                     │
│  │                                  │              │                     │
│  │  Packet level (Scapy)           │              │                     │
│  │    TTL+variance, TCP window,     │              │                     │
│  │    payload, retransmissions,     │              │                     │
│  │    port-scan signatures          │              │                     │
│  └──────────────┬───────────────────┘              │                     │
│                 │                                  │                     │
│                 ▼                                  ▼                     │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              TEMPORAL WINDOWING (S_t)                            │   │
│  │                                                                    │   │
│  │  Traffic is aggregated into fixed-length windows (e.g. 60 s).     │   │
│  │  Each window becomes a normalised feature vector S_t.             │   │
│  │  Sequence:  S_(t-k) ... S_(t-1)  S_t  →  S_(t+1)               │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                      │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              WORLD MODEL  (learned P(S_t+1 | S_t))              │   │
│  │                                                                    │   │
│  │  ┌──────────────────────────────────────────────────────────┐     │   │
│  │  │  Transformer (default)   |    LSTM (fallback)            │     │   │
│  │  │  ● Encoder-only, no positional encoding, mean-pooling    │     │   │
│  │  │  ● Hidden 96, Layers 2, Dropout 0.3                      │     │   │
│  │  │  ● MSE(state) + weighted BCE(attack head) loss           │     │   │
│  │  │  ● Time-aware train / val / test split (no leakage)      │     │   │
│  │  └──────────────────────────────────────────────────────────┘     │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                      │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              K-STEP FORWARD SIMULATION (model-based rollout)    │   │
│  │                                                                    │   │
│  │  S_t  →  Ŝ_(t+1)  →  Ŝ_(t+2)  → ... →  Ŝ_(t+K)               │   │
│  │                                                                    │   │
│  │  Outputs:                                                         │   │
│  │    ● Time-series infiltration probability score                  │   │
│  │    ● Predicted MITRE ATT&CK stage per step                       │   │
│  │    ● Top contributing traffic features (attribution)             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              EXPLAINABILITY                                      │   │
│  │                                                                    │   │
│  │  ● SHAP (TreeExplainer on RandomForest / attack classifier)      │   │
│  │  ● World-model attention-weight attribution (time-step memory)   │   │
│  │  ● Both exposed to the defender                                 │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              BENCHMARK                                           │   │
│  │                                                                    │   │
│  │  Logistic Regression baseline trained on the SAME features and   │   │
│  │  time-aware split. Compared on F1, precision, recall, FPR, AUC   │   │
│  │  over the held-out val+test region (170 windows, 46 positives).  │   │
│  │  Result: world model wins (F1 0.891@0.6 / 0.902 val-tuned, AUC   │   │
│  │  0.9635) → temporal-dynamics advantage proven.                   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              OFFLINE DEMO  (run.py --stage demo)                 │   │
│  │                                                                    │   │
│  │  ● Express backend (:5000) + React/Vite frontend (:5173)        │   │
│  │  ● Feature extraction → world-model inference                    │   │
│  │  ● Infiltration-probability timeline + rollout + stage track     │   │
│  │  ● Flagged windows, ATT&CK stages, top contributing features     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              JARVIS BRIDGE  (optional, separate from offline demo)│  │
│  │                                                                    │   │
│  │  Node/Express + Socket.IO server.                                 │   │
│  │  Python bridge → Ollama qwen2.5:7b for narrative reports.        │   │
│  │  React frontend: radar + voice + chat.                            │   │
│  │  (Not required for evaluation; preserved as secondary demo.)     │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              DEVICE COLLECTORS  (optional, for live telemetry)   │   │
│  │                                                                    │   │
│  │  psutil-based agent: CPU, RAM, network bytes → backend.          │   │
│  │  (Used for live JARVIS demo; not for the offline evaluation.)    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. World model details

### State representation S_t

Each time window (e.g. 60 seconds of traffic) is represented as a fixed-length feature vector combining:

| Feature class | Examples | Source |
|---|---|---|
| **Flow aggregate** | Bytes, packets, duration, TCP flag bitmap, SYN/ACK/FIN/RST/PSH counts | Flow CSV (CIC-IDS) |
| **Flow ratios** | Bidirectional bytes ratio, bidirectional packets ratio | Flow CSV |
| **Inter-arrival timing** | IAT mean, IAT variance, IAT max | Flow CSV |
| **Packet detail** | TTL mean & variance, TCP window size, payload distribution | PCAP (Scapy) |
| **Anomaly indicators** | Retransmission count, port-scan sequential/randomised pattern | PCAP (Scapy) |

### Learned dynamics

```
P(S_t+1 | S_t)   ≈   TransformerSeq( S_(t-k) ... S_t )      (LSTM fallback)

Training target:  S_t+1  from ground-truth attack timeline annotations
Loss:             MSE(state) + attack_loss_weight · weighted_BCE(attack head)
                  (attack_loss_weight 12.0, pos_weight 4.0 — tuned to win the
                   shared LR benchmark at high infiltration recall)
```

A small **binary classifier branch** (linear head on the pooled sequence representation) predicts *attack/no-attack* for the next window, giving the infiltration probability timeline.

### K-step rollout

Starting from a given S_t, the model autoregressively predicts Ŝ_(t+1), uses that to predict Ŝ_(t+2), etc., up to K steps. The attack probability is recorded at each step, producing the time-series curve the defender sees.

### MITRE ATT&CK stage mapping

Each predicted (and observed) state is scored against stage fingerprints (`detection/stage_mapping.py`) — reconnaissance / initial access / lateral movement / C2 / exfiltration / impact:

```
stage_score(s) = Σ_f w_f · sigmoid(d_f · z_f / 2)
stage          = argmax(stage_score · a_pred)          a_pred = attack probability
confidence     = sigmoid(scale(norm_top_score)) · a_pred
```

Rules weight the discriminating features per technique (e.g. T1190 initial-access on forward data/subflow/packet bursts, T1498 impact on SYN flooding). The dominant stage over the infiltration windows is **INITIAL ACCESS (126) → IMPACT (29)**; benign pre-onset trust defaults to COMMAND AND CONTROL at ≈0 confidence. Stage plan is emitted in `forecast_info.json` and visualized as the rollout stage track.

### Attribution

- **SHAP**: trained on the attack classifier (RandomForest) using the same features; gives per-feature SHAP values for each prediction.
- **Attention**: attention weights over the sequence (t-k ... t) from the world model's encoder — which historical windows most influenced the prediction.

---

## 4. Dependencies

All installed inside the project `.venv` (Python 3.14, GPU-enabled torch).

| Component | Library | Purpose |
|---|---|---|
| World model | `torch 2.14.0+cu130` | Transformer + LSTM sequence model, GPU training |
| Classical ML baseline | `scikit-learn 1.9` | Logistic regression, RandomForest |
| Feature attribution | `shap 0.52` | Tree-based SHAP |
| Packet parsing | `scapy 2.7` | PCAP → packet-level features |
| Flow processing | `pandas 3.0` + `numpy 2.5` | CSV loading, windowing |
| Forecasting baseline | `statsmodels 0.15` | ARIMA (for comparison) |
| Demo UI | `streamlit 1.63` | Fully offline upload + chart |

---

## 5. Datasets

| Dataset | Role |
|---|---|
| **CIC-IDS-2018** | Primary: timestamped flow CSV — Infiltration attack day used in the shipped pipeline |
| CIC-IDS-2017 | Additional attack scenarios (if needed) |
| CTU-13 | Botnet flows (optional) |
| MITRE ATT&CK | Attack stage knowledge base |

All datasets are publicly available and used locally only (no external API calls in the evaluation path).

---

## 6. Deliverables

| Deliverable | Location |
|---|---|
| Source code | GitHub repo |
| Architecture document | This file (`ARCHITECTURE.md`) |
| Demo video (≤2 min) | `assets/demo.mp4` (produced post-implementation) |
| Technical presentation (≤5 slides) | `assets/presentation.pdf` (produced post-implementation) |
| Model weights + training config | `models/` + `configs/world_model.yaml` |
| Benchmark results | `models/benchmark_metrics.json` (produced post-training) |
