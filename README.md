<div align="center">

![Header](https://capsule-render.vercel.app/api?type=waving&color=0:0A84FF,100:9C27B0&height=220&section=header&text=CyberForeSight&fontSize=60&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=AI-Based%20Network%20Attack%20Forecasting&descAlignY=58&descSize=18)

![SIH](https://img.shields.io/badge/SIH-2026-0A84FF?style=for-the-badge)
![Cybersecurity](https://img.shields.io/badge/CYBERSECURITY-NTRO-E53935?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-WORLD%20MODELS-9C27B0?style=for-the-badge)
![Python](https://img.shields.io/badge/PYTHON-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PYTORCH-DEEP%20LEARNING-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)

<br>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=22&pause=700&color=00D9FF&center=true&vCenter=true&width=900&lines=OBSERVE+NETWORK+BEHAVIOUR;LEARN+TEMPORAL+NETWORK+STATES;SIMULATE+K-STEP+FUTURE+STATES;FORECAST+ATTACK+PROGRESSION;EXPLAIN+THE+PREDICTION;DEFEND+BEFORE+COMPROMISE)](https://git.io/typing-svg)

![divider](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif)

</div>

---

## 🚨 From Detection to Prediction

Traditional IDS asks:

> **"Is the network under attack?"**

CyberForeSight asks:

> **"Where is the network heading next?"**

CyberForeSight learns how network behaviour changes over time and uses a **Temporal World Model** to simulate future network states and forecast possible attack progression.

---

<div align="center">

## ⚡ CyberForeSight in Action


[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=18&pause=1000&color=9C27B0&center=true&vCenter=true&width=800&lines=Live+Traffic+%E2%86%92+Live+Forecast;Every+Second+Counts+in+Cyber+Defence)](https://git.io/typing-svg)

</div>

---

# 🧠 How It Works

```text
       📡 NETWORK TRAFFIC
              │
              ▼
      🔎 FLOW + PACKET
          FEATURES
              │
              ▼
       🧩 NETWORK STATE
            S(t)
              │
              ▼
    ┌─────────────────────┐
    │    🌍 WORLD MODEL   │
    │                     │
    │ P(Sₜ₊₁ | Sₜ)        │
    │                     │
    │ Temporal Transformer│
    │ + LSTM / GNN        │
    └──────────┬──────────┘
               │
               ▼
       🔮 K-STEP ROLLOUT
               │
               ▼
     Sₜ → Sₜ₊₁ → Sₜ₊₂ → ... → Sₜ₊ₖ
               │
               ▼
       ⚠️ THREAT FORECAST
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
  Probability Stage    Risk
       │       │        │
       └───────┼────────┘
               ▼
          💡 EXPLAIN
        SHAP + ATTENTION
               │
               ▼
       🛡️ DEFENDER
       DECISION SUPPORT
```

---

# 🎯 Core Capabilities

|    📡 TELEMETRY    |      🧠 WORLD MODEL     |   🔮 FORECASTING  |
| :----------------: | :---------------------: | :---------------: |
| Flow + Packet Data | Temporal State Learning | K-Step Simulation |

|    🎯 ATT&CK   | 💡 EXPLAINABLE AI |      🔐 AUDIT      |
| :------------: | :---------------: | :----------------: |
| Attack Mapping |  SHAP + Attention | Evidence Integrity |

---

# 🌍 World Model

The **World Model is the core intelligence of CyberForeSight.**

Instead of simply classifying traffic, it learns how network states evolve over time.

```text
Sₜ
 │
 ▼
Sₜ₊₁
 │
 ▼
Sₜ₊₂
 │
 ▼
Sₜ₊₃
 │
 ▼
 ...
 │
 ▼
Sₜ₊ₖ
```

The model learns:

```text
P(Sₜ₊₁ | Sₜ)
```

### Primary Model

```text
🌍 Temporal Transformer
```

### Comparative Models

```text
LSTM
GNN
Hybrid Temporal Models
```

---

# 🔮 K-Step Threat Forecasting

CyberForeSight goes beyond:

```text
"ATTACK DETECTED"
```

It looks ahead:

```text
CURRENT
   │
   ▼
 S(t)
   │
   ▼
 S(t+1)
   │
   ▼
 S(t+2)
   │
   ▼
 S(t+3)
   │
   ▼
  ...
   │
   ▼
 S(t+K)
```

The predicted states produce:

```text
┌────────────────────────────┐
│ ⚠️ THREAT PROBABILITY      │
│ 🎯 LIKELY ATTACK STAGE     │
│ 📈 RISK / CONFIDENCE       │
│ 🔮 FUTURE STATE TREND      │
│ 💡 CONTRIBUTING FEATURES   │
└────────────────────────────┘
```

---

# 🔎 Network Intelligence

CyberForeSight combines **flow-level + packet-level telemetry**.

### Flow Features

```text
Source IP
Destination IP
Source Port
Destination Port
Protocol
Bytes
Packets
Duration
TCP Flags
Inter-Arrival Time
Bidirectional Ratios
```

### Packet Features

```text
TTL
TTL Variance
TCP Window
Packet Length
Payload Size
Fragmentation
Retransmissions
Port Scan Indicators
```

These are transformed into **time-windowed network states**.

---

# 💡 Explainable AI

Predictions should not be a black box.

```text
             AI PREDICTION
                   │
          ┌────────┴────────┐
          ▼                 ▼
       🧮 SHAP          🧠 ATTENTION
          │                 │
          ▼                 ▼
  Important Features   Important Time
                       Patterns
          │                 │
          └────────┬────────┘
                   ▼
             💡 EXPLANATION
```

### Example

```text
Top Contributing Features

██████████████████  Packet Rate
████████████████    Flow Duration
████████████        Destination Port
██████████          TCP Flags
████████            TTL Variance
```

---

# 🎯 Threat Intelligence

Predictions can be enriched using established cybersecurity knowledge.

```text
        THREAT FORECAST
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
 MITRE      CAPEC     NVD
 ATT&CK
     │        │        │
     └────────┼────────┘
              ▼
       SECURITY CONTEXT
```

### Knowledge Sources

* **MITRE ATT&CK** → Adversary tactics and techniques
* **CAPEC** → Common attack patterns
* **NIST NVD** → Vulnerability / CVE context
* **NCIIPC** → Indian Critical Information Infrastructure context

---

# 🗃️ Datasets

| Dataset                                                              | Purpose                         |
| ---------------------------------------------------------------------| -------------------------------- |
| [CIC-IDS2017](https://www.unb.ca/cic/datasets/ids-2017.html)         | Network intrusion traffic       |
| [CIC-IDS2018](https://www.unb.ca/cic/datasets/ids-2018.html)         | Modern attack scenarios         |
| [UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset) | Network attack behaviour        |
| [CTU-13](https://www.stratosphereips.org/datasets-ctu13)             | Botnet traffic                  |
| [CICIoT2023](https://www.unb.ca/cic/datasets/iotdataset-2023.html)   | IoT attack behaviour            |
| [LANL Cyber Datasets](https://csr.lanl.gov/data/)                    | Authentication and cyber events |
| [DARPA IDS](https://www.ll.mit.edu/r-d/datasets)                     | Historical intrusion scenarios  |

---

# 🧰 Technology Stack

<div align="center">

### 🤖 AI / Machine Learning

![AI Stack](https://skillicons.dev/icons?i=python,pytorch,sklearn)

### 🖥️ Application / Development

![Development Stack](https://skillicons.dev/icons?i=git,github,sqlite,streamlit,bash)

</div>

### Additional Technologies

```text
📡 Scapy / PyShark      → Packet & PCAP processing
📊 Pandas / NumPy       → Data processing
💡 SHAP                 → Explainable AI
🎯 MITRE ATT&CK         → Threat intelligence
🧩 CAPEC                → Attack patterns
🔍 NVD                  → Vulnerability context
🗄️ SQLite / Parquet     → Local storage
🔐 Permissioned Ledger  → Prediction integrity
```

---

# 🏗️ Architecture

![CyberForeSight Architecture](assets/architecture.png)

```text
📡 DATA
   ↓
🔎 FEATURE ENGINEERING
   ↓
⏱️ TEMPORAL WINDOWING
   ↓
🧩 NETWORK STATE
   ↓
🌍 WORLD MODEL
   ↓
🔮 K-STEP ROLLOUT
   ↓
⚠️ THREAT FORECAST
   ↓
💡 EXPLAINABILITY
   ↓
🛡️ DEFENDER DASHBOARD
   ↓
🔐 AUDIT TRAIL
```

---

# 🔐 Prediction Integrity

Sensitive network data remains **off-chain**.

```text
        🚨 ALERT / PREDICTION
                 │
                 ▼
          Evidence Hash
                 │
                 ▼
       Prediction Metadata
                 │
                 ▼
       🔐 Permissioned Ledger
                 │
                 ▼
        Tamper-Evident Audit
```

```text
❌ Raw PCAP → Blockchain

✅ Evidence Hash → Blockchain
✅ Metadata → Blockchain
✅ Raw PCAP → Local / Off-Chain Storage
```

---

# 🖥️ Local-First Deployment

```text
             PRIVATE NETWORK
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    💻 CLIENT    💻 CLIENT    💻 CLIENT
        │           │           │
        └───────────┼───────────┘
                    ▼
          ┌─────────────────┐
          │  🛡️ JARVIS /   │
          │ CyberForeSight   │
          └────────┬────────┘
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
        🌍 AI     🔮       💡
       MODEL    FORECAST  EXPLAIN
          │        │        │
          └────────┼────────┘
                   ▼
          🖥️ DEFENDER UI
```

---

# 📊 Expected Output

```text
╔════════════════════════════════════╗
║       🛡️ CYBERFORSIGHT             ║
║          THREAT FORECAST           ║
╠════════════════════════════════════╣
║                                    ║
║ ⚠️ Threat Probability : HIGH       ║
║ 🔮 Forecast Horizon   : K Steps    ║
║ 🎯 Predicted Stage    : Forecast   ║
║ 📈 Risk Level         : HIGH       ║
║                                    ║
╠════════════════════════════════════╣
║ 💡 TOP CONTRIBUTING FEATURES       ║
║                                    ║
║ • Abnormal Flow Rate               ║
║ • Destination Port Behaviour       ║
║ • TCP Flag Pattern                 ║
║ • Packet Burst Activity            ║
║                                    ║
╚════════════════════════════════════╝
```

---

# 🔄 Continuous Learning

```text
       📡 NETWORK TRAFFIC
               │
               ▼
          🔮 FORECAST
               │
               ▼
        🛡️ DEFENDER
          FEEDBACK
               │
               ▼
       FALSE POSITIVES /
       NEW ATTACK SAMPLES
               │
               ▼
        📈 DRIFT DETECTION
               │
               ▼
         🧠 MODEL UPDATE
               │
               ▼
        🔮 BETTER FORECAST
```

---

# 📁 Repository Structure

```text
CyberForeSight/
│
├── 📄 README.md
│
├── 🖼️ assets/
│   ├── architecture.png
│   └── cyberforsight-flow.gif
│
├── 📂 data/
│   ├── raw/
│   └── processed/
│
├── 📂 src/
│   ├── ingestion/
│   ├── features/
│   ├── preprocessing/
│   ├── state/
│   ├── world_model/
│   ├── forecasting/
│   ├── explainability/
│   ├── threat_mapping/
│   └── dashboard/
│
├── 📂 models/
├── 📂 configs/
├── 📂 notebooks/
├── 📂 tests/
│
├── 📄 requirements.txt
└── 📄 run.py
```

---

# ▶️ Quick Start

### Clone

```bash
git clone https://github.com/YOUR-ORG/CyberForeSight.git
cd CyberForeSight
```

### Create Environment

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

### Install

```bash
pip install -r requirements.txt
```

### Run

```bash
python run.py
```

### Dashboard

```bash
streamlit run src/dashboard/app.py
```

---

# 🤝 Collaborative Development

```text
        💡 IDEA
          │
          ▼
       📋 ISSUE
          │
          ▼
    🌿 FEATURE BRANCH
          │
          ▼
       💻 CODE
          │
          ▼
       🧪 TEST
          │
          ▼
    🔀 PULL REQUEST
          │
          ▼
     👀 CODE REVIEW
          │
          ▼
       ✅ MERGE
```

### Branch Example

```bash
git checkout -b feature/world-model
git add .
git commit -m "Add temporal world model"
git push origin feature/world-model
```

Then create a Pull Request.

---

# 👥 Contributors

<div align="center">

<a href="https://github.com/YOUR-ORG/CyberForeSight/graphs/contributors">

<img src="https://contrib.rocks/image?repo=YOUR-ORG/CyberForeSight">

</a>

<br>

### Built collaboratively by the CyberForeSight Team 🛡️

</div>

---

# 📈 Evaluation

```text
Precision
Recall
F1-Score
False Positive Rate
Forecast Accuracy
Attack-Stage Accuracy
Inference Latency
Forecast-Horizon Performance
```

### Baseline

```text
        LOGISTIC REGRESSION
                 │
                 ▼
             COMPARISON
                 ▲
                 │
      CYBERFORSIGHT WORLD MODEL
```

Time-aware train / validation / test splits should be used to reduce temporal leakage.

---

# 📚 Research Foundation

| Research                                                                                                  | Contribution                 |
| --------------------------------------------------------------------------------------------------------- | ---------------------------- |
| [World Models](https://arxiv.org/abs/1803.10122)                                                          | Learned environment dynamics |
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762)                                             | Transformer architecture     |
| [Graph Networks](https://proceedings.mlr.press/v119/sanchez-gonzalez20a.html)                             | Learned state transitions    |
| [SHAP](https://papers.nips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html) | Explainable predictions      |

---

# 🛡️ Responsible Use

CyberForeSight is intended for:

```text
✓ Defensive Cybersecurity
✓ Security Monitoring
✓ Threat Forecasting
✓ Network Research
✓ Authorized Testing
```

Use only on networks and data for which appropriate authorization exists.

---

<div align="center">

![divider](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.gif)

# 🚀 The Vision

```text
DETECT
   ↓
UNDERSTAND
   ↓
SIMULATE
   ↓
FORECAST
   ↓
EXPLAIN
   ↓
DEFEND
```

<br>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=21&pause=900&color=00D9FF&center=true&vCenter=true&width=850&lines=Don't+just+detect+the+attack.;Understand+where+the+network+is+heading.;CyberForeSight+%7C+Predictive+Cyber+Defence)](https://git.io/typing-svg)

<br>

### 🛡️ CyberForeSight

### **Observe • Learn • Simulate • Forecast • Explain • Defend**

**SIH 2026 | AI + Network Security + World Models**

![Footer](https://capsule-render.vercel.app/api?type=waving&color=0:9C27B0,100:0A84FF&height=120&section=footer)

</div>
