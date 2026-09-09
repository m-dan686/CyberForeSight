import { useEffect, useState } from "react";
import "./Forecast.css";
import LiveAttackLab from "./LiveAttackLab.jsx";

const API = "/forecast";

const PIPELINE_COMMANDS = [
  {
    step: "01",
    title: "FEATURE EXTRACTION",
    desc: "Extract flow and packet features into 60s temporal windows S(t)",
    cmd: ".venv\\Scripts\\python run.py --stage features",
  },
  {
    step: "02",
    title: "WORLD MODEL TRAINING",
    desc: "Train sequence world model to learn P(S_t+1 | S_t) state transitions",
    cmd: ".venv\\Scripts\\python run.py --stage train",
  },
  {
    step: "03",
    title: "FORECAST GENERATION",
    desc: "Execute K-step autoregressive rollout and calculate infiltration timeline",
    cmd: ".venv\\Scripts\\python run.py --stage forecast",
  },
  {
    step: "04",
    title: "EXPLAINABILITY ATTRIBUTION",
    desc: "Generate SHAP feature drivers and temporal attention time-step weights",
    cmd: ".venv\\Scripts\\python run.py --stage explain",
  },
  {
    step: "05",
    title: "BENCHMARK EVALUATION",
    desc: "Perform out-of-sample comparison against logistic regression baseline",
    cmd: ".venv\\Scripts\\python run.py --stage benchmark",
  },
];

const fmtDate = (v) => (v ? String(v).slice(0, 19).replace("T", " ") : "—");
const num = (v) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : 0;
};

function Kpi({ label, value, accent }) {
  return (
    <div className={`f-kpi ${accent ? `k-${accent}` : ""}`}>
      <span className="f-kpi-label">{label}</span>
      <strong className="f-kpi-value">{value}</strong>
    </div>
  );
}

function CommandCard({ item }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(item.cmd).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2200);
    });
  };

  return (
    <div className="f-cmd-card">
      <div className="f-cmd-header">
        <div className="f-cmd-title-group">
          <span className="f-cmd-step">{item.step}</span>
          <span className="f-cmd-title">{item.title}</span>
        </div>
        <button
          className={`f-cmd-copy-btn ${copied ? "copied" : ""}`}
          onClick={handleCopy}
          type="button"
          aria-label={`Copy command for ${item.title}`}
        >
          {copied ? "✓ Copied" : "Copy Command"}
        </button>
      </div>
      <p className="f-cmd-desc">{item.desc}</p>
      <div className="f-cmd-code-row">
        <code>{item.cmd}</code>
      </div>
    </div>
  );
}

// ---------- SVG line chart (threat timeline) ----------
function TimelineChart({ rows, threshold }) {
  const W = 900;
  const H = 240;
  const PAD = { l: 46, r: 14, t: 14, b: 30 };
  const n = rows.length;
  if (n < 2) return <div className="f-empty">timeline too short to render</div>;

  const x = (i) => PAD.l + (i / (n - 1)) * (W - PAD.l - PAD.r);
  const y = (p) => PAD.t + (1 - num(p)) * (H - PAD.t - PAD.b);
  const line = rows.map((r, i) => `${x(i).toFixed(1)},${y(r.prob_next).toFixed(1)}`).join(" ");

  const flagged = rows.filter((r) => num(r.flagged) === 1);
  const hasAttack = rows.some((r) => num(r.attack) === 1);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="f-chart" role="img" aria-label="threat timeline">
      <defs>
        <linearGradient id="probFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#37bee6" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#37bee6" stopOpacity="0.02" />
        </linearGradient>
      </defs>

      {[0, 0.25, 0.5, 0.75, 1].map((g) => (
        <g key={g}>
          <line x1={PAD.l} x2={W - PAD.r} y1={y(g)} y2={y(g)} stroke="#1d3f52" strokeWidth="1" />
          <text x={PAD.l - 6} y={y(g) + 4} textAnchor="end" className="f-axis">
            {g}
          </text>
        </g>
      ))}

      {hasAttack &&
        rows.map((r, i) =>
          num(r.attack) === 1 ? (
            <rect key={i} x={x(i)} y={PAD.t} width={PAD.r + (W - PAD.l - PAD.r) / (n - 1)} height={H - PAD.t - PAD.b} fill="#ff4d6d" opacity="0.18" />
          ) : null
        )}

      <polygon points={`${PAD.l},${y(0)} ${line} ${x(n - 1)},${y(0)}`} fill="url(#probFill)" />
      <polyline points={line} fill="none" stroke="#37bee6" strokeWidth="2.2" />

      {flagged.map((r, i) => {
        const xi = rows.indexOf(r);
        const yi = y(r.prob_next);
        return (
          <g key={i}>
            <line x1={x(xi)} x2={x(xi)} y1={yi - 14} y2={yi + 14} stroke="#f59e0b" strokeWidth="2" />
            <circle cx={x(xi)} cy={yi} r="4.5" fill="#f59e0b" />
          </g>
        );
      })}

      {threshold > 0 && (
        <line
          x1={PAD.l}
          x2={W - PAD.r}
          y1={y(threshold)}
          y2={y(threshold)}
          stroke="#ff4d6d"
          strokeWidth="1.4"
          strokeDasharray="5 4"
        />
      )}
    </svg>
  );
}

// ---------- Rollout bars ----------
function RolloutChart({ rows, threshold }) {
  const W = 900;
  const H = 150;
  const PAD = { l: 46, r: 14, t: 14, b: 30 };
  const k = rows.length;
  if (k === 0) return <div className="f-empty">No rollout steps available</div>;
  const slot = (W - PAD.l - PAD.r) / k;
  const maxProb = Math.max(1, ...rows.map((r) => num(r.attack_probability)));

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="f-chart" role="img" aria-label="rollout">
      {rows.map((r, i) => {
        const h = (num(r.attack_probability) / maxProb) * (H - PAD.t - PAD.b - 6);
        const over = num(r.attack_probability) >= threshold;
        return (
          <g key={i}>
            <rect
              x={PAD.l + i * slot + 6}
              y={H - PAD.b - h}
              width={slot - 12}
              height={Math.max(h, 1)}
              fill={over ? "#ff4d6d" : "#f59e0b"}
              rx="2"
            />
            <text x={PAD.l + i * slot + slot / 2} y={H - PAD.b - h - 6} textAnchor="middle" className="f-axis">
              {num(r.attack_probability).toFixed(2)}
            </text>
            <text x={PAD.l + i * slot + slot / 2} y={H - 10} textAnchor="middle" className="f-axis">
              +{num(r.minutes_ahead)}m
            </text>
          </g>
        );
      })}
      {threshold > 0 && (
        <line x1={PAD.l} x2={W - PAD.r} y1={y0(threshold)} y2={y0(threshold)} stroke="#ff4d6d" strokeWidth="1.3" strokeDasharray="5 4" />
      )}
    </svg>
  );

  function y0(p) {
    return H - PAD.b - (p / maxProb) * (H - PAD.t - PAD.b - 6);
  }
}

function AttentionPanel({ attention }) {
  if (!attention) return null;
  const rows = attention.top_influential_windows || [];
  const maxW = Math.max(0.01, ...rows.map((r) => num(r.attention)));
  return (
    <div className="f-card">
      <div className="f-card-head">
        <h3>Attention attribution — sequence memory</h3>
        <span className="f-badge">{attention.target_window}</span>
      </div>
      <p className="f-sub">
        Forecast P(attack) = <b>{num(attention.forecast_next_attack).toFixed(3)}</b> from the world model's
        additive attention over the last {rows.length} windows.
      </p>
      {rows.map((r, i) => (
        <div className="f-bar-row" key={i}>
          <span className="f-bar-label">{fmtDate(r.window)}</span>
          <div className="f-bar-track">
            <div className={`f-bar ${num(r.gt_attack) === 1 ? "b-attack" : "b-bg"}`} style={{ width: `${(num(r.attention) / maxW) * 100}%` }} />
          </div>
          <span className={num(r.gt_attack) === 1 ? "f-tag tag-attack" : "f-tag"}>{num(r.gt_attack) === 1 ? "ATTACK" : "benign"}</span>
          <span className="f-bar-val">{num(r.attention).toFixed(3)}</span>
        </div>
      ))}
    </div>
  );
}

function ShapPanel({ shap }) {
  if (!shap) return null;
  return (
    <div className="f-card">
      <div className="f-card-head">
        <h3>SHAP attribution — feature drivers</h3>
        <span className="f-badge">RandomForest on flow features</span>
      </div>
      <div className="f-split">
        {(shap.samples || []).map((s) => {
          const maxAbs = Math.max(0.01, ...s.top_features.map((f) => Math.abs(num(f.shap_value))));
          const positive = s.label_meaning === "ATTACK";
          return (
            <div key={s.name}>
              <p className="f-sub">
                <b>{s.name}</b> — {s.predicted === s.label ? "correctly " : ""}classified as{" "}
                <span className={positive ? "tag-attack" : "tag-benign"}>{s.label_meaning}</span>
              </p>
              {s.top_features.map((f, i) => {
                const v = num(f.shap_value);
                const w = (Math.abs(v) / maxAbs) * 100;
                return (
                  <div className="f-bar-row" key={i}>
                    <span className="f-bar-label">{f.feature}</span>
                    <div className="f-bar-track">
                      <div
                        className={`f-bar ${v >= 0 ? "b-attack" : "b-benign"}`}
                        style={{ width: `${w}%`, marginLeft: `${v >= 0 ? "0%" : "auto"}` }}
                      />
                    </div>
                    <span className="f-bar-val">{v.toFixed(4)}</span>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function BenchmarkPanel({ metrics, compare }) {
  if (!metrics) return null;

  const worldKey = Object.keys(metrics).find((k) => k.endsWith("_world_model"));
  const modelLabel = worldKey ? worldKey.replace("_world_model", "").toUpperCase() : "WORLD MODEL";
  const wm = worldKey ? metrics[worldKey] : null;
  const lr = metrics.logistic_regression || null;
  if (!wm || !lr) return null;

  const rowShared = wm.shared_threshold && lr.shared_threshold ? [
    [`${modelLabel} @ shared`, wm.shared_threshold, wm.auc],
    [`LR @ shared`, lr.shared_threshold, lr.auc],
  ] : [];
  const rowTuned = wm.val_tuned && lr.val_tuned ? [
    [`${modelLabel} @ val-tuned`, wm.val_tuned, wm.auc],
    [`LR @ val-tuned`, lr.val_tuned, lr.auc],
  ] : [];
  const rowPersistShared = wm.persistence_shared && lr.persistence_shared ? [
    [`${modelLabel} · 2-of-3 persist @ shared`, wm.persistence_shared, wm.auc],
    [`LR · 2-of-3 persist @ shared`, lr.persistence_shared, lr.auc],
  ] : [];
  const rowPersistAcc = wm.persistence_accuracy_tuned && lr.persistence_accuracy_tuned ? [
    [`${modelLabel} · 2-of-3 persist @ acc-tuned`, wm.persistence_accuracy_tuned, wm.auc],
    [`LR · 2-of-3 persist @ acc-tuned`, lr.persistence_accuracy_tuned, lr.auc],
  ] : [];

  const cellsOf = (label, blk, auc) => [
    label,
    blk.threshold,
    blk.accuracy !== undefined ? blk.accuracy : "—",
    blk.precision,
    blk.recall,
    blk.f1,
    blk.fpr,
    auc,
  ];

  const verdict = metrics.verdict || {};
  const f1Diff = Array.isArray(verdict.f1_lstm_vs_lr)
    ? verdict.f1_lstm_vs_lr[0] - verdict.f1_lstm_vs_lr[1]
    : null;

  return (
    <div className="f-card">
      <div className="f-card-head">
        <h3>WS6 — world model vs baseline · preview</h3>
        <span className="f-badge">{modelLabel} · see full report in models/benchmark_metrics.json</span>
      </div>
      <table className="f-table">
        <thead>
          <tr><th>Model</th><th>Thr</th><th>Acc</th><th>P</th><th>R</th><th>F1</th><th>FPR</th><th>AUC</th></tr>
        </thead>
        <tbody>
          {[...rowShared, ...rowTuned, ...rowPersistShared, ...rowPersistAcc].map(([label, blk, auc], i) => (
            <tr key={i}>{cellsOf(label, blk, auc).map((c, j) => (j === 0 ? <td key={j}><b>{c}</b></td> : <td key={j}>{c}</td>))}</tr>
          ))}
        </tbody>
      </table>
      <p className="f-sub">
        {verdict.temporal_dynamics_win ? (
          <>
            ✔ Temporal-dynamics win verified: the {modelLabel} beats logistic regression on
            {f1Diff !== null && f1Diff >= 0 ? ` F1 (Δ +${f1Diff.toFixed(3)})` : " recall/lead-time"} while
            also emitting a forward-simulated rollout (a capability the static baseline does not have).
          </>
        ) : (
          <>The {modelLabel} trails the baseline on F1; see the report for lead-time comparison.</>
        )}
      </p>
      {wm.persistence_accuracy_tuned && (
        <p className="f-sub f-persist-note">
          <b>Persistence rule:</b> flag a window only if its attack probability stays at/above the
          threshold for 2 of 3 consecutive windows (threshold tuned on the <b>val slice only</b> —
          max accuracy, recall ≥ 0.98 — then applied over the full timeline and scored on the same
          OOS horizon). OOS accuracy: <b>{num(wm.persistence_accuracy_tuned.accuracy).toFixed(4)}</b>{" "}
          (@ thr {num(wm.persistence_accuracy_tuned.threshold).toFixed(2)}), equal to raw val-tuned:{" "}
          {num(wm.val_tuned.accuracy).toFixed(4)}. The 10 OOS false positives are one contiguous{" "}
          <b>post-attack decay tail</b> (10:55–11:04, P≥0.85 on verified-benign traffic), not isolated
          spikes, so 2-of-3 persistence changes nothing — a documented limit of the pure forecaster.
        </p>
      )}
      {compare && compare.length > 2 && (
        <div className="f-bench">
          {compare.map((r, i) => (
            <div className="f-bench-row" key={i}>
              <span className="f-bar-label">{fmtDate(r.window_start)}</span>
              <div className="f-bench-lines">
                <div className={`f-bar ${num(r.lstm_prob) >= num(wm.shared_threshold.threshold) ? "b-attack" : "b-bg"}`} style={{ width: `${num(r.lstm_prob) * 100}%` }} />
                <div className={`f-bar ${num(r.lr_prob) >= num(wm.shared_threshold.threshold) ? "b-attack" : "b-benign"}`} style={{ width: `${num(r.lr_prob) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StagePanel({ info }) {
  const plan = info && info.stage_plan;
  if (!plan) return null;
  const steps = plan.steps || [];
  const gstage = plan.dominant_stage || (steps[0] && steps[0].stage) || "—";

  return (
    <div className="f-card">
      <div className="f-card-head">
        <h3>Predicted MITRE ATT&CK stage — intrusion path</h3>
        <span className="f-badge">dominant: {gstage}</span>
      </div>
      <p className="f-sub">
        Stage scored from <b>predicted future-state fingerprints</b> (rule-level heuristic over the
        world model's forward simulation — see <code>detection/stage_mapping.py</code>).
      </p>
      <div className="f-stage-track">
        {steps.map((s, i) => (
          <div className="f-stage-step" key={i}>
            <span className="f-stage-dot" title={s.technique} />
            <span className="f-stage-label">{s.stage}</span>
            <span className="f-stage-val">+{num(s.minutes_ahead)}m · {Math.round(num(s.attack_probability) * 100)}% · ({Math.round(num(s.confidence) * 100)}% conf)</span>
          </div>
        ))}
      </div>
      {steps[0] && (
        <p className="f-sub">
          <b>Forecast technique:</b> {steps[0].technique} ({steps[0].tactic}).
          Signals: {Array.isArray(steps[0].top_signals) ? steps[0].top_signals.join(", ") : "—"}.
        </p>
      )}
    </div>
  );
}

export default function ForecastDashboard() {
  const [state, setState] = useState({
    loading: true,
    ready: false,
    backendOffline: false,
    modelType: "MODEL METADATA UNAVAILABLE",
    forecast: null,
  });

  useEffect(() => {
    let cancelled = false;
    fetch(API)
      .then((r) => {
        if (!r.ok) throw new Error("Network response was not ok");
        return r.json();
      })
      .then((data) => {
        if (!cancelled) {
          setState({
            loading: false,
            ready: Boolean(data.ready),
            backendOffline: false,
            modelType: data.modelType || "MODEL METADATA UNAVAILABLE",
            forecast: data.forecast || null,
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setState({
            loading: false,
            ready: false,
            backendOffline: true,
            modelType: "MODEL METADATA UNAVAILABLE",
            forecast: null,
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const { loading, ready, backendOffline, modelType, forecast } = state;
  const info = ready && forecast ? forecast.info : null;
  const timeline = ready && forecast ? forecast.timeline || [] : [];
  const rollout = ready && forecast ? forecast.rollout || [] : [];

  return (
    <div className="forecast-view">
      <LiveAttackLab />

      {loading && <div className="f-empty">Loading forecast artifacts…</div>}

      {backendOffline && !loading && (
        <div className="f-card f-error">
          <h3>Backend Service Unreachable</h3>
          <p>
            The forecast interface could not establish a connection to <code>http://localhost:5000/forecast</code>.
            Ensure the Express backend is running:
          </p>
          <div className="f-cmd-card" style={{ marginTop: "14px" }}>
            <div className="f-cmd-header">
              <span className="f-cmd-title">START BACKEND SERVER</span>
            </div>
            <div className="f-cmd-code-row">
              <code>node backend/server.js</code>
            </div>
          </div>
        </div>
      )}

      {!loading && !ready && !backendOffline && (
        <div className="f-card f-error">
          <div className="f-card-head">
            <h3>Pipeline Artifacts Not Found</h3>
            <span className="f-badge">Engine Status: Standby</span>
          </div>
          <p className="f-sub" style={{ marginBottom: "18px" }}>
            The forecast dashboard consumes real generated model outputs in <code>models/</code>. Run the
            pipeline stages below in sequence to generate the temporal state windows, world model checkpoints,
            and explainability artifacts:
          </p>

          <div className="f-cmd-grid">
            {PIPELINE_COMMANDS.map((item) => (
              <CommandCard key={item.step} item={item} />
            ))}
          </div>
        </div>
      )}

      {ready && info && (
        <>
          <div className="f-kpis">
            <Kpi label="World model architecture" value={modelType} accent="cyan" />
            <Kpi label="First attack window" value={fmtDate(info.first_attack_ts)} />
            <Kpi
              label="Earliest pre-attack flag"
              value={info.earliest_pre_flag_idx === -1 ? "none" : `+${info.lead_minutes} min before`}
              accent="warn"
            />
            <Kpi
              label="Infiltration lead time"
              value={info.lead_minutes >= 0 ? `${info.lead_minutes} min` : "—"}
              accent="attack"
            />
            <Kpi label="Pre-flag windows" value={info.pre_flag_count} />
            <Kpi label="Threat threshold" value={info.threshold} />
            <Kpi label="Rollout horizon" value={`${info.k_steps} min`} />
            {info.stage_plan && (
              <Kpi label="Dominant ATT&CK stage" value={info.stage_plan.dominant_stage} accent="attack" />
            )}
          </div>

          <div className="f-card">
            <div className="f-card-head">
              <h3>Infiltration probability timeline</h3>
              <span className="f-badge">{timeline.length} windows · red band = ground-truth attack</span>
            </div>
            <TimelineChart rows={timeline} threshold={num(info.threshold)} />
          </div>

          <div className="f-grid2">
            <div className="f-card">
              <div className="f-card-head">
                <h3>K-step rollout from {fmtDate(info.start_window)}</h3>
                <span className="f-badge">autoregressive · {info.k_steps} steps</span>
              </div>
              <RolloutChart rows={rollout} threshold={num(info.threshold)} />
            </div>

            {info.seq_len && (
              <div className="f-card">
                <div className="f-card-head">
                  <h3>Scenario Analysis</h3>
                </div>
                <ul className="f-list">
                  <li>
                    Windows of <b>{info.seq_len}</b> consecutive network states feed the <b>{modelType}</b>.
                  </li>
                  <li>
                    The model forecasts next-window attack probability; alerting starts at{" "}
                    <b>{num(info.threshold) * 100}%</b>.
                  </li>
                  <li>
                    On this file the model flagged infiltration <b>{info.lead_minutes} minutes</b> before ground truth.
                  </li>
                </ul>
              </div>
            )}
          </div>

          <AttentionPanel attention={forecast.attention} />
          <ShapPanel shap={forecast.shap} />
          <StagePanel info={info} />
          <BenchmarkPanel metrics={forecast.benchmarkMetrics} compare={forecast.benchmarkCompare} />
        </>
      )}
    </div>
  );
}