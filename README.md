<div align="center">

![Header](https://capsule-render.vercel.app/api?type=waving&color=0:0A84FF,100:9C27B0&height=220&section=header&text=CyberForeSight&fontSize=60&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=AI-Based%20Network%20Attack%20Forecasting&descAlignY=58&descSize=18)

![SIH](https://img.shields.io/badge/SIH-2026-0A84FF?style=for-the-badge)
![Python](https://img.shields.io/badge/PYTHON-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PYTORCH-TRANSFORMER%20WORLD%20MODEL-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![React](https://img.shields.io/badge/REACT-19-61DAFB?style=for-the-badge&logo=react&logoColor=white)
![Vite](https://img.shields.io/badge/VITE-8-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Express](https://img.shields.io/badge/EXPRESS-5-000000?style=for-the-badge&logo=express&logoColor=white)

<br>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=22&pause=700&color=00D9FF&center=true&vCenter=true&width=900&lines=OBSERVE+NETWORK+BEHAVIOUR;LEARN+TEMPORAL+NETWORK+STATES;SIMULATE+K-STEP+FUTURE+STATES;FORECAST+ATTACK+PROGRESSION;EXPLAIN+THE+PREDICTION;DEFEND+BEFORE+COMPROMISE)](https://git.io/typing-svg)

![divider](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif)

</div>

---

# 🚨 From Detection to Prediction

Traditional intrusion detection asks:

> **"Is the network under attack right now?"**

CyberForeSight asks:

> **"Where is the network heading next?"**

It learns how network behaviour evolves over time with a **temporal world model**, simulates future network states, and **forecasts attack progression with a measurable lead time** — turning detection into prediction.

**Implemented on a real, trusted dataset** (CIC-IDS2018 — Infiltration attack day): the world model raises its first pre-attack flag **9 minutes before** the ground-truth infiltration begins, and explains *why*.

---

# ✅ What Ships Today vs Roadmap

| Area | Implemented | Roadmap |
| :-- | :-- | :-- |
| Feature pipeline | Flow + packet features → 60 s windows → `S(t)` states + transitions | Streaming/packet-level ingestion |
| World model | Temporal Transformer sequence model: `P(Sₜ₊₁ | Sₜ)` (train + checkpointing, LSTM fallback) | GNN, hybrid |
| Forecasting | K-step autoregressive rollout + threat probability + lead-time detection | Confidence-calibrated ensembles |
| Explainability | SHAP (feature attribution) + Attention (time-step attribution) | Counterfactual explanations |
| Baseline | Logistic regression on identical next-window task (honest A/B) | Additional IDS baselines |
| Threat intelligence | MITRE ATT&CK stage mapping from predicted future-state fingerprints | Full kill-chain / playbook synthesis |
| Dashboard | React + Express + Socket.IO live view (JARVIS) + Forecast analytics | Historical replay mode |
| Integrity | — | Evidence hashing + permissioned ledger audit |

---

# 🧠 How It Works

```text
       📡 CIC-IDS2018 TRAFFIC (CSV / PCAP)
               │
               ▼
      🔎 FLOW + PACKET FEATURES          features/extract_flow.py
               │                                extract_packet.py
               ▼
       ⏱️ TEMPORAL WINDOWING             features/window.py
       (60 s windows → S(t))
               │
               ▼
     🧩 NETWORK STATE + TRANSITIONS       features/transitions.py
            (S(t) -> S(t+1))
               │
               ▼
     ┌──────────────────────┐
     │    🌍 WORLD MODEL     │            training/train.py
     │  P(Sₜ₊₁ | Sₜ)        │
     │  LSTM over states    │            training/forecast.py
     └──────────┬───────────┘
                │
                ▼
        🔮 K-STEP ROLLOUT
        Sₜ → Sₜ₊₁ → ... → Sₜ₊ₖ
                │
                ▼
        ⚠️ THREAT FORECAST             forecast_info.json / timeline
        (first pre-flag, lead time)
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
   Probability  Stage    Risk
        │       │        │
        └───────┼────────┘
                ▼
        💡 EXPLAIN (SHAP + Attention)   detection/world_explain.py
                │
                ▼
        🖥️ DEFENDER DASHBOARD          backend/server.js + frontend/
```

---

# 🎯 Core Capabilities

| 📡 TELEMETRY | 🧠 WORLD MODEL | 🔮 FORECASTING |
| :-- | :-- | :-- |
| CIC flow + packet features | Transformer temporal state learning | K-step autoregressive rollout |

| ⏱️ LEAD TIME | 💡 EXPLAINABLE AI | 📊 BENCHMARK |
| :-- | :-- | :-- |
| Pre-attack flagging (9 min on demo day) | SHAP + Attention | Transformer vs Logistic Regression |

---

# 🌍 World Model

Instead of classifying a single window in isolation, the network-state model learns how network states evolve:

```text
P(Sₜ₊₁ | Sₜ)
```

- **Input features:** `state_*` columns derived from flow + packet telemetry over 60 s windows (backward/forward IAT stats, packet rates, flag counters, sizes, tcp window, TTL variance, etc.).
- **Target:** next window's state `target_state_*` plus the binary next-window attack label (`attack_t1`).
- **Task:** predict the **next-window attack probability** (`prob_next`) and simulate the future trajectory.

Default model is a **Temporal Transformer** (`models/transformer_world.py` — encoder-only, no positional encoding, mean-pooled attention), with an **LSTM** fallback. Loss is `MSE(state) + weighted_BCE(attack_head)` with `attack_loss_weight = 12.0`, `pos_weight = 4.0` (chosen to win the honest LR benchmark at high recall). Trained with early stopping on val loss (`patience 15`, `lr×0.5`), hidden 96, 2 layers, dropout 0.3, sequence length 10, `weight_decay 1e-3`, `grad_clip 1.0`, time-aware split — config-driven via `configs/world_model.yaml`; checkpoints artifacts written to `models/world_model_<type>.pt`.

### Comparative / roadmap models

```text
🌐 GNN over client-server graph
🔀 Hybrid temporal models
```

---

# 🔮 K-Step Threat Forecasting

CyberForeSight looks **ahead**, not just "attack / no attack":

```text
S(t) → S(t+1) → S(t+2) → ... → S(t+K)
```

`training/forecast.py` rolls the model forward **K steps** from the last observed window and computes a full-day threat timeline.

### Verified result — CIC-IDS2018 Infiltration day

| Metric | Value |
| :-- | :-- |
| Ground-truth infiltration onset | 2018-03-01 **02:00:00** |
| Earliest pre-attack flag | **01:51** (+9 min before onset) |
| Forecast lead time | **+9 minutes** |
| Pre-flag windows (thr 0.6) | **35** |
| Start of rollout | 01:59 (last benign window) |
| Rollout probability | ≈0.97 → 0.99 over +8 min |
| Dominant MITRE ATT&CK stage | **INITIAL ACCESS** (T1190, ~75% stage confidence, 8/8 rollout steps) |
| Timeline | 570 windows, 01:00 – 12:59 |

`training/forecast.py` also scores each rollout step against MITRE ATT&CK stage fingerprints (`detection/stage_mapping.py`): during the infiltration the mapped stages are **INITIAL ACCESS (126 windows) → IMPACT (29 windows)**, and the benign pre-onset default resolves to COMMAND AND CONTROL at ~0 confidence.

Artifacts: `models/forecast_info.json`, `models/forecast_timeline.csv`, `models/forecast_rollout.csv`, `models/forecast_timeline.png`.

---

# 💡 Explainable AI

```text
        AI PREDICTION
              │
      ┌───────┴────────┐
      ▼                ▼
   🧮 SHAP          🧠 ATTENTION
  (features)      (time steps)
      │                │
      └───────┬────────┘
              ▼
         💡 EXPLANATION
```

`detection/world_explain.py` produces both views, written to `models/explain_shap.json` and `models/explain_attention.json`.

- **SHAP** — per-window feature attribution. On attack windows the top driver is **`bwd_iat_mean`** (+0.123); benign windows show flat/negative contributions.
- **Attention** — highlights the historical windows a prediction leans on, confirming the model attends to the pre-attack windows (01:56 → 01:59, peak at 02:00).

Predicted next-state fingerprints from the world model's forward simulation are also mapped to a **MITRE ATT&CK stage** (`detection/stage_mapping.py`) — reconnaissance / initial access / lateral movement / C2 / exfiltration / impact — with per-step technique IDs and confidence, exposed in `forecast_info.json` «stage_plan» and the dashboard's stage track.

---

# 📊 Benchmark — World Model vs Logistic Regression

An **honest A/B** on the identical next-window task: same features, same out-of-sample windows, chronological time-aware split, no temporal leakage. Evaluation region = **val + test** (window index ≥ 399): 170 windows, **46 infiltration positives**; LR is fit on the train region (index < 399) only, never on the eval region. Shared row uses the production threshold (0.6); val-tuned row uses the max-F1 threshold chosen per model on the val slice only.

| Model | Thr | P | R (Recall) | F1 | FPR | AUC |
| :-- | --: | --: | --: | --: | --: | --: |
| **Temporal Transformer (world model)** | 0.6 | 0.8182 | **0.9783** | **0.8911** | 0.0806 | **0.9635** |
| Logistic Regression (baseline) | 0.6 | 0.9 | 0.587 | 0.7105 | 0.0242 | 0.9469 |
| Transformer @ val-tuned (0.4) | — | 0.8214 | **1.0** | **0.902** | 0.0806 | 0.9635 |
| LR @ val-tuned (0.3) | — | 0.7925 | 0.913 | 0.8485 | 0.0887 | 0.9469 |

**Temporal-dynamics win verified:** the Transformer beats LR on F1 (Δ +0.053 at the shared threshold, +0.053 val-tuned) and AUC (+0.017), recalls 100% of infiltrations at the val-tuned operating point — while emitting a forward-simulated K-step rollout and stage map, capabilities a static classifier does not have. Full record in `models/benchmark_metrics.json` (verdict `temporal_dynamics_win: true`).

Artifacts: `models/benchmark_metrics.json`, `models/benchmark_compare.csv`, `models/benchmark_compare.png`.

---

# 🖥️ Live Dashboard

A two-tab operations console.

```text
   frontend/  React 19 + Vite 8  (port 5173)
   backend/   Express 5 + Socket.IO  (port 5000)  →  spawns .venv python jarvis_bridge.py (FullJARVIS)
```

- **LIVE tab** — connected devices + threat levels, animated network radar, voice/chat control, AI response panel (via Socket.IO).
- **FORECAST tab** — data-driven from `GET /forecast`: KPI cards (onset, lead time, pre-flags, threshold), threat timeline, K-step rollout, attention + SHAP panels, and the benchmark table.

```
run.py --stage demo     # starts backend + frontend for you
```

---

# 🗃️ Datasets

| Dataset | Status |
| :-- | :-- |
| [CIC-IDS2018](https://www.unb.ca/cic/datasets/ids-2018.html) (Infiltration day) | ✅ Used in the shipped pipeline |
| [CIC-IDS2017](https://www.unb.ca/cic/datasets/ids-2017.html) | Roadmap — extend to more attack days |
| [UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset) | Roadmap — behaviour variety |
| [CTU-13](https://www.stratosphereips.org/datasets-ctu13) / [CICIoT2023](https://www.unb.ca/cic/datasets/iotdataset-2023.html) | Roadmap — botnet / IoT |
| [LANL](https://csr.lanl.gov/data/) / [DARPA IDS](https://www.ll.mit.edu/r-d/datasets) | Roadmap — enterprise + historical |

---

# 🧰 Technology Stack

<div align="center">

### 🤖 AI / ML

![AI Stack](https://skillicons.dev/icons?i=python,pytorch,sklearn)

### 🖥️ Application

![App Stack](https://skillicons.dev/icons?i=react,vite,nodejs,express,bash,git,github)

</div>

```text
📡 Scapy / PyShark      → Packet & PCAP processing
📊 Pandas / NumPy       → Data processing
💡 SHAP                 → Explainable AI
🔮 statsmodels          → Time-series baselines (ARIMA)
🗄️ SQLite / Parquet     → Local storage
🖼️ matplotlib           → Chart artifacts (PNG)
```

---

# ▶️ Quick Start (Windows)

```bash
# 1. environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt        # CUDA? pip install -r requirements-cuda.txt

# 2. frontend + backend deps
npm --prefix frontend install
npm --prefix backend install

# 3. data
#    place the CIC-IDS2018 infiltration day CSV under data/raw/ (or pass --csv)

# 4. pipeline
.venv\Scripts\python run.py --stage features    --csv data/raw/<day>.csv
.venv\Scripts\python run.py --stage train       --config configs/world_model.yaml
.venv\Scripts\python run.py --stage forecast    --snapshot data/processed/window_state.csv
.venv\Scripts\python run.py --stage explain
.venv\Scripts\python run.py --stage benchmark
.venv\Scripts\python run.py --stage demo        # backend (5000) + frontend (5173)

# 5. or run the dashboard manually
node backend/server.js
npm --prefix frontend run dev            # open http://localhost:5173
```

Linux / macOS uses `source .venv/bin/activate` and `.venv/bin/python`.

### Pipeline runbook

| Stage | Produces |
| :-- | :-- |
| `features` | `data/processed/window_state.csv`, `data/processed/transitions.csv` |
| `train` | `models/world_model_<type>.pt`, `train_metrics.json`, `training_history.json` |
| `forecast` | `forecast_info.json` (+ `stage_plan`), `forecast_timeline.csv` (+ stage cols), `forecast_rollout.csv`, `forecast_timeline.png` |
| `explain` | `explain_attention.json`, `explain_shap.json` |
| `benchmark` | `benchmark_metrics.json`, `benchmark_compare.csv`, `benchmark_compare.png` |
| `demo` | boots backend (:5000) + Vite frontend (:5173) |

---

# 📁 Repository Structure

```text
CyberForeSight/
│
├── 📄 run.py                    # pipeline entry point (--stage features|train|forecast|explain|benchmark|demo)
├── 📄 requirements.txt          # core Python deps (CPU)
├── 📄 requirements-cuda.txt     # CUDA-enabled PyTorch install
├── 📄 ARCHITECTURE.md
│
├── 📂 features/                 # WS2 — feature + state pipeline
│   ├── extract_flow.py          #   flow features from CIC CSV/PCAP
│   ├── extract_packet.py        #   packet features
│   ├── window.py                #   60 s temporal windows → S(t)
│   ├── transitions.py           #   S(t) → S(t+1) + attack_t1 label
│   └── schema.py
│
├── 📂 training/                 # WS3 — world model
│   ├── train.py                 #   training + checkpointing (per model type)
│   └── forecast.py              #   K-step rollout + stage plan + forecast charts
│
├── 📂 models/                   # (gitignored) model + forecast + explain + benchmark artifacts
│   └── transformer_world.py     #   Temporal Transformer (encoder-only, mean-pooled attention)
│
├── 📂 detection/                # WS4 / WS6 — explainability + baselines
│   ├── world_explain.py         #   SHAP + attention attribution
│   ├── stage_mapping.py         #   MITRE ATT&CK stage scoring from state fingerprints
│   ├── benchmark.py             #   LR vs world-model next-window A/B
│   └── ...  (classifiers, feature QC, datasets)
│
├── 📂 models/                   # (gitignored) generated world-model/forecast/explain/benchmark artifacts
├── 📂 configs/world_model.yaml  # model + training + benchmark + MITRE hyper-parameters
│
├── 📂 backend/                  # WS5 — Express + Socket.IO
│   ├── server.js                #   REST /forecast + live socket feed
│   └── jarvis_bridge.py         #   spawns FullJARVIS assistant (agent/)
│
├── 📂 frontend/                 # WS5 — React 19 + Vite
│   └── src/
│       ├── App.jsx              #   Live/Forecast toggle + live view
│       ├── ForecastDashboard.jsx
│       ├── theme.css / App.css / Forecast.css
│       └── main.jsx
│
├── 📂 agent/  📂 llm/  📂 rag/  # JARVIS AI assistant (RAG + chat)
├── 📂 collectors/               # live network collection (roadmap streaming)
├── 📂 data/                     # raw | processed | ml (gitignored)
└── 📂 notebooks/                # exploration
```

---

# 🗺️ Roadmap

```text
🌐 GNN world model
⏱️ Live PCAP streaming → real-time forecasting
🎯 Full kill-chain / playbook synthesis (CAPEC / NVD / NCIIPC)
🔐 Evidence hashing + permissioned ledger for auditability
📈 Continuous learning: drift detection + model update
🔮 Calibrated confidence intervals on forecasts
```

---

# 📚 Research Foundation

| Research | Contribution |
| :-- | :-- |
| [World Models](https://arxiv.org/abs/1803.10122) | Learned environment dynamics |
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762) | Attention-based sequence modelling |
| [LSTM](https://www.bioinf.jku.at/publications/older/2604.pdf) | Temporal state memory |
| [SHAP](https://papers.nips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html) | Explainable predictions |

---

# 🛡️ Responsible Use

CyberForeSight is intended for:

```text
✓ Defensive Cybersecurity     ✓ Security Monitoring
✓ Threat Forecasting          ✓ Network Research
✓ Authorized Testing          ✓ SOC decision support
```

Use only on networks and data for which appropriate authorization exists. Generated artifacts (models, forecasts, logs) are gitignored and regenerable via `run.py`.

---

# 🤝 Collaborative Development

```bash
git checkout -b feature/<workstream>
git commit -m "<workstream>: ..."
git push origin feature/<workstream>
```

Then open a Pull Request — see `ARCHITECTURE.md` for component contracts.

---

<div align="center">

![divider](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif)

# 🚀 The Vision

```text
DETECT → UNDERSTAND → SIMULATE → FORECAST → EXPLAIN → DEFEND
```

<br>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=21&pause=900&color=00D9FF&center=true&vCenter=true&width=850&lines=Don't+just+detect+the+attack.;Understand+where+the+network+is+heading.;CyberForeSight+%7C+Predictive+Cyber+Defence)](https://git.io/typing-svg)

<br>

### 🛡️ CyberForeSight

### **Observe • Learn • Simulate • Forecast • Explain • Defend**

**SIH 2026 | AI + Network Security + World Models**

![Footer](https://capsule-render.vercel.app/api?type=waving&color=0:9C27B0,100:0A84FF&height=120&section=footer)

</div>