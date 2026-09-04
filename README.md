# 🛡️ CyberForSight

## AI-Based Network Attack Forecasting with a Temporal World Model

```{=html}
<p align="center">
```
`<b>`{=html}From detecting attacks to forecasting what may happen
next.`</b>`{=html}`<br>`{=html} CyberForSight learns how a network
evolves over time and simulates future network states to support
proactive cyber defence.
```{=html}
</p>
```
```{=html}
<p align="center">
```
`<img src="https://img.shields.io/badge/AI-Cybersecurity-0A2540?style=for-the-badge">`{=html}
`<img src="https://img.shields.io/badge/World%20Model-Temporal%20Forecasting-1F6FEB?style=for-the-badge">`{=html}
`<img src="https://img.shields.io/badge/Explainable-AI-2E8B57?style=for-the-badge">`{=html}
`<img src="https://img.shields.io/badge/Deployment-Local--First-6A5ACD?style=for-the-badge">`{=html}
```{=html}
</p>
```
> **Project:** CyberForSight\
> **Team:** ACHIEVERS\
> **SIH Problem Statement:** SIH26153 --- AI based Network Attack
> Forecasting from Network Traffic Data\
> **Organization:** National Technical Research Organisation (NTRO)\
> **Theme:** Blockchain & Cybersecurity

------------------------------------------------------------------------

## 🎬 Animated Demo

Add the final demonstration GIF at `assets/cyberforsight-demo.gif`:

```{=html}
<p align="center">
```
`<img src="assets/cyberforsight-demo.gif" width="850" alt="CyberForSight animated demo">`{=html}
```{=html}
</p>
```

------------------------------------------------------------------------

## 🚀 What It Does

CyberForSight is a **local-first predictive cybersecurity prototype**
that learns changing network behaviour from traffic telemetry and
forecasts how malicious activity could progress over future time
windows.

Instead of asking only **"Is this traffic malicious?"**, it asks:

> **"Given the current network state, what could happen next?"**

### Core capabilities

-   📡 Multi-level packet and flow telemetry
-   ⚙️ Feature engineering and temporal windowing
-   🧩 Network-state representation
-   🌍 Temporal World Model learning state-transition dynamics
-   🔮 K-step future-state simulation
-   ⚠️ Threat probability and attack-stage forecasting
-   🗺️ MITRE ATT&CK contextual mapping
-   💡 SHAP and attention-based explainability
-   🛡️ Defender decision support
-   🔐 Tamper-evident audit using hashes / permissioned blockchain
-   🔄 Analyst feedback, drift detection and retraining

------------------------------------------------------------------------

## 🧠 Core Architecture

``` text
NETWORK TRAFFIC
      ↓
FEATURES + TEMPORAL WINDOWS
      ↓
NETWORK STATE S(t)
      ↓
┌──────────────────────────────────┐
│       TEMPORAL WORLD MODEL       │
│       learns state dynamics      │
│       P(Sₜ₊₁ | Sₜ)               │
└──────────────────────────────────┘
      ↓
K-STEP FUTURE SIMULATION
Sₜ → Sₜ₊₁ → … → Sₜ₊ₖ
      ↓
THREAT FORECAST
Probability + Attack Stage + Risk
      ↓
EXPLAIN → DECIDE → DEFEND
```

### World Model

The predictive core learns:

**P(Sₜ₊₁ \| Sₜ)**

where `Sₜ` is the current network state and future states are
recursively generated through K-step rollout.

The forecast is a **probabilistic risk estimate**, not a guaranteed
prediction.

------------------------------------------------------------------------

## 📊 Network Telemetry

### Flow-level

-   Source / destination IP and port
-   Protocol and TCP flags
-   Duration
-   Bytes and packets
-   Inter-arrival-time statistics
-   Forward / backward ratios
-   Connection behaviour

### Packet-level

-   TTL and TTL variance
-   TCP window characteristics
-   Packet / payload size
-   Fragmentation
-   Retransmissions
-   Port-scan indicators
-   Protocol anomalies

------------------------------------------------------------------------

## 🧪 Model Pipeline

### Current Detection

A **Random Forest** baseline can classify current traffic and provide a
benchmark.

### Temporal World Model

The main forecasting layer uses a temporal sequence model, with
**Temporal Transformer / attention** as the primary direction and
LSTM/GNN as alternative research paths.

### K-Step Rollout

``` text
Sₜ
 ↓
World Model → Sₜ₊₁
                 ↓
              Sₜ₊₂
                 ↓
                ...
                 ↓
              Sₜ₊ₖ
                 ↓
Threat Probability + Stage + Risk
```

### Explainability

-   SHAP feature attribution
-   Attention-based temporal importance
-   Top contributing traffic features
-   Relevant MITRE ATT&CK context

------------------------------------------------------------------------

## 🗂️ Datasets

  -----------------------------------------------------------------------
  Dataset                             Main Use
  ----------------------------------- -----------------------------------
  **CIC-IDS2017**                     Labeled network intrusion and
                                      attack traffic

  **CIC-IDS2018**                     Attack scenarios and traffic
                                      features

  **UNSW-NB15**                       Normal/attack traffic and multiple
                                      attack types

  **CTU-13**                          Botnet scenarios and labeled flows

  **CICIoT2023**                      IoT attacks and network behaviour

  **LANL Cyber Security Datasets**    Authentication, DNS, process and
                                      network events

  **DARPA IDS**                       Historical intrusion-detection
                                      scenarios
  -----------------------------------------------------------------------

### Official Dataset Links

-   [CIC-IDS2017](https://www.unb.ca/cic/datasets/ids-2017.html)
-   [CIC-IDS2018](https://www.unb.ca/cic/datasets/ids-2018.html)
-   [UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset)
-   [CTU-13](https://www.stratosphereips.org/datasets-ctu13)
-   [CICIoT2023](https://www.unb.ca/cic/datasets/iotdataset-2023.html)
-   [LANL Cyber Security Datasets](https://csr.lanl.gov/data/)
-   [DARPA IDS Datasets](https://www.ll.mit.edu/r-d/datasets)

------------------------------------------------------------------------

## 🗺️ Threat Knowledge & Research

  -----------------------------------------------------------------------
  Reference                           Role
  ----------------------------------- -----------------------------------
  **MITRE ATT&CK Enterprise**         Tactics, techniques and adversary
                                      progression

  **CAPEC**                           Common attack-pattern knowledge

  **NIST NVD**                        CVE and vulnerability context

  **NCIIPC**                          Indian Critical Information
                                      Infrastructure context

  **Ha & Schmidhuber (2018)**         World Models and learned dynamics

  **Vaswani et al. (2017)**           Transformer / attention modelling

  **Sanchez-Gonzalez et al. (2020)**  Learned state transitions and
                                      simulation

  **Lundberg & Lee (2017)**           SHAP explainability
  -----------------------------------------------------------------------

### Research Links

-   [MITRE ATT&CK
    Enterprise](https://attack.mitre.org/matrices/enterprise/)
-   [CAPEC](https://capec.mitre.org/)
-   [NIST NVD](https://www.nist.gov/itl/nvd)
-   [NCIIPC](https://nciipc.gov.in/)
-   [World Models](https://arxiv.org/abs/1803.10122)
-   [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
-   [Graph Network-based
    Simulators](https://proceedings.mlr.press/v119/sanchez-gonzalez20a.html)
-   [SHAP
    paper](https://papers.nips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html)

------------------------------------------------------------------------

## 🔬 Training & Validation

``` text
Dataset
  ↓
Cleaning → Feature Extraction → Temporal Alignment
  ↓
Sequence / Window Construction
  ↓
Network-State Construction
  ↓
State-Transition Targets
  ↓
World Model Training
  ↓
Time-Based Validation
  ↓
Versioned Model
```

Because the goal is **future forecasting**, time-based
train/validation/test splitting is preferred to reduce temporal leakage.

Benchmark metrics: - Precision - Recall - F1-score - False Positive
Rate - Forecast performance at multiple horizons

**No fabricated performance values are claimed; results should be
reported only after reproducible experiments.**

------------------------------------------------------------------------

## 🛡️ Defender Decision Support

The dashboard focuses on:

  Question                    Output
  --------------------------- ----------------------------
  What is happening?          Current network state
  Is there risk?              Threat probability / trend
  What may happen next?       K-step forecast
  What behaviour is likely?   ATT&CK context
  Why?                        SHAP / attention evidence

CyberForSight is intended as **decision support**, not autonomous
incident response.

------------------------------------------------------------------------

## 🔐 Integrity & Blockchain

Only selected metadata and cryptographic hashes are intended for the
audit layer.

``` text
Prediction / Alert
       ↓
Evidence Metadata
       ↓
Cryptographic Hash
       ↓
Permissioned Audit Ledger
```

**On-chain:** alert ID, timestamp, model version, evidence hash and
selected metadata.

**Off-chain:** raw PCAP, payloads, large feature files and sensitive
traffic data.

------------------------------------------------------------------------

## 🧰 Technology Stack

**Python • PyTorch • Scikit-learn • Scapy/PyShark • SHAP •
Streamlit/Flask • CSV/PCAP/Parquet • SQLite • MITRE ATT&CK • CAPEC • NVD
• Local RAG/Vector Store • Permissioned Blockchain**

------------------------------------------------------------------------

## 📁 Repository Structure

``` text
CyberForSight/
├── data/
├── features/
├── models/
│   ├── random_forest/
│   └── world_model/
├── forecasting/
├── explainability/
├── dashboard/
├── audit/
├── configs/
├── notebooks/
├── tests/
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

## 👥 Team Workstreams

**Member 1 --- Data & Telemetry:** dataset acquisition, PCAP/flow
processing, features and preprocessing.

**Member 2 --- Detection & World Model:** Random Forest baseline,
network-state representation and temporal model.

**Member 3 --- Forecasting & Explainability:** K-step rollout, threat
probability, ATT&CK mapping, SHAP and attention.

**Member 4 --- Platform & Security:** dashboard, audit
hashing/blockchain, integration and testing.

------------------------------------------------------------------------

## 🎯 Expected Deliverables

-   Source code and reproducible configuration
-   Preprocessing and feature-extraction pipeline
-   Trained model weights/checkpoints
-   K-step forecasting engine
-   Explainability module
-   ATT&CK-based threat context
-   Local dashboard / CLI
-   Integrity and audit mechanism
-   Architecture and deployment documentation
-   Baseline comparison
-   Demonstration video

------------------------------------------------------------------------

## ⚠️ Responsible Use

CyberForSight is intended for **authorized defensive-security research,
security monitoring and controlled experimentation**.

Predictions represent probabilistic model outputs and should be reviewed
by human defenders.

------------------------------------------------------------------------

## 🌟 Vision

> **Observe → Understand → Simulate → Forecast → Explain → Defend**

CyberForSight moves network security from reactive detection toward
**proactive, explainable threat forecasting**.

```{=html}
<p align="center">
```
`<b>`{=html}🛡️ CyberForSight --- Predict the Threat. Explain the Risk.
Defend Earlier.`</b>`{=html}
```{=html}
</p>
```
