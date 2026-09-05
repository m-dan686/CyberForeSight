<div align="center">

![Header](https://capsule-render.vercel.app/api?type=waving&color=0:0A84FF,100:9C27B0&height=220&section=header&text=CyberForeSight&fontSize=60&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=AI-Based%20Network%20Attack%20Forecasting&descAlignY=58&descSize=18)

![SIH](https://img.shields.io/badge/SIH-2026-0A84FF?style=for-the-badge)
![Python](https://img.shields.io/badge/PYTHON-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PYTORCH-LSTM%20WORLD%20MODEL-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
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

**Implemented on a real, trusted dataset** (CIC-IDS2018 — Infiltration attack day): the world model raises its first pre-attack flag **2 minutes before** the ground-truth infiltration begins, and explains *why*.

---

# ✅ What Ships Today vs Roadmap

| Area | Implemented | Roadmap |
| :-- | :-- | :-- |
| Feature pipeline | Flow + packet features → 60 s windows → `S(t)` states + transitions | Streaming/packet-level ingestion |
| World model | LSTM sequence model: `P(Sₜ₊₁ | Sₜ)` (train + checkpointing) | Temporal Transformer, GNN, hybrid |
| Forecasting | K-step autoregressive rollout + threat probability + lead-time detection | Confidence-calibrated ensembles |
| Explainability | SHAP (feature attribution) + Attention (time-step attribution) | Counterfactual explanations |
| Baseline | Logistic regression on identical next-window task (honest A/B) | Additional IDS baselines |
| Dashboard | React + Express + Socket.IO live view (JARVIS) + Forecast analytics | Historical replay mode |
| Threat intelligence | — | MITRE ATT&CK / CAPEC / NVD / NCIIPC mapping |
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
| CIC flow + packet features | LSTM temporal state learning | K-step autoregressive rollout |

| ⏱️ LEAD TIME | 💡 EXPLAINABLE AI | 📊 BENCHMARK |
| :-- | :-- | :-- |
| Pre-attack flagging (≈2 min on demo day) | SHAP + Attention | LSTM vs Logistic Regression |

---

# 🌍 World Model

Instead of classifying a single window in isolation, the LSTM learns how network states evolve:

```text
P(Sₜ₊₁ | Sₜ)
```

- **Input features:** `state_*` columns derived from flow + packet telemetry over 60 s windows (backward/forward IAT stats, packet rates, flag counters, sizes, tcp window, TTL variance, etc.).
- **Target:** next window's state `target_state_*` plus the binary next-window attack label (`attack_t1`).
- **Task:** predict the **next-window attack probability** (`prob_next`) and simulate the future trajectory.

Trained for **25 epochs** (smoke run) with `weight_decay = 1e-5`, sequence length 8, hidden size 64 — train loss `3.02 → 1.45`, val loss `3.36 → 3.39`. Config-driven via `configs/world_model.yaml`; artifacts written to `models/`.

### Comparative / roadmap models

```text
🌍 Temporal Transformer
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
| Earliest pre-attack flag | **01:58** (6 flags raised) |
| Forecast lead time | **+2 minutes** |
| Start of rollout | 01:59 (last benign window) |
| Rollout probability | 0.76 → 0.98 over +8 min |
| Timeline | 560 windows, 01:09 – 12:58 |

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

---

# 📊 Benchmark — LSTM vs Logistic Regression

An **honest A/B** on the identical next-window task (same features, same evaluation windows, chronological split, no temporal leakage). Same 168 out-of-sample windows with 43 infiltration windows:

| Model | Accuracy | Recall (Infiltration) | False-Positive Rate | AUC |
| :-- | --: | --: | --: | --: |
| **Logistic Regression** (baseline) | **0.8452** | — | 0.032 | **0.9473** |
| **LSTM World Model** (25-epoch smoke) | 0.8214 | 0.3953 | 0.032 | 0.8845 |

The linear baseline edges out the undertrained 25-epoch LSTM on this near-linear signal — expected. The LSTM's value is in **sequence memory, attention, and leading the onset by minutes**. Closing the gap is a matter of training budget (80+ epochs, LR schedule).

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
| `train` | `models/world_model_lstm.pt`, `train_metrics.json`, `training_history.json` |
| `forecast` | `forecast_info.json`, `forecast_timeline.csv`, `forecast_rollout.csv`, `forecast_timeline.png` |
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
│   ├── train.py                 #   LSTM training + checkpointing
│   └── forecast.py              #   K-step rollout + forecast charts
│
├── 📂 detection/                # WS4 / WS6 — explainability + baselines
│   ├── world_explain.py         #   SHAP + attention attribution
│   ├── benchmark.py             #   LR vs LSTM next-window A/B
│   └── ...  (classifiers, feature QC, datasets)
│
├── 📂 models/                   # (gitignored) generated LSTM/forecast/explain/benchmark artifacts
├── 📂 configs/world_model.yaml  # LSTM hyper-parameters
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
🌍 Temporal Transformer + GNN world model
⏱️ Live PCAP streaming → real-time forecasting
🎯 MITRE ATT&CK / CAPEC / NVD / NCIIPC mapping
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