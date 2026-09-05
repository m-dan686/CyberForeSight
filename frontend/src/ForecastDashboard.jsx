import { useEffect, useState } from "react";
import "./Forecast.css";

const API = "http://localhost:5000/forecast";

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
              +{num(r.minutes_ahead)}
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
        Forecast P(attack) = <b>{num(attention.forecast_next_attack).toFixed(3)}</b> from the LSTM's
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
  const rows = [
    ["Model", "Accuracy", "Precision", "Recall", "FPR", "AUC"],
    ["LSTM world model", ...Object.values(metrics.lstm_world_model)],
    ["Logistic regression", ...Object.values(metrics.logistic_regression)],
  ];
  return (
    <div className="f-card">
      <div className="f-card-head">
        <h3>WS6 — world model vs baseline</h3>
        <span className="f-badge">
          {metrics.horizon_windows} eval windows · {metrics.n_infiltration_eval} infiltration
        </span>
      </div>
      <table className="f-table">
        <thead>
          <tr>{rows[0].map((h, i) => <th key={i}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.slice(1).map((r, i) => (
            <tr key={i}>{r.map((c, j) => (j === 0 ? <td key={j}><b>{c}</b></td> : <td key={j}>{c}</td>))}</tr>
          ))}
        </tbody>
      </table>
      {compare && compare.length > 2 && (
        <div className="f-bench">
          {compare.map((r, i) => (
            <div className="f-bench-row" key={i}>
              <span className="f-bar-label">{fmtDate(r.window_start)}</span>
              <div className="f-bench-lines">
                <div className={`f-bar ${num(r.lstm_prob) >= num(metrics.threshold) ? "b-attack" : "b-bg"}`} style={{ width: `${num(r.lstm_prob) * 100}%` }} />
                <div className={`f-bar ${num(r.lr_prob) >= num(metrics.threshold) ? "b-attack" : "b-benign"}`} style={{ width: `${num(r.lr_prob) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ForecastDashboard() {
  const [state, setState] = useState({ loading: true, ready: false, forecast: null });

  useEffect(() => {
    let cancelled = false;
    fetch(API)
      .then((r) => r.json())
      .then((data) => {
        if (!cancelled) setState({ loading: false, ready: data.ready, forecast: data.forecast });
      })
      .catch(() => {
        if (!cancelled) setState({ loading: false, ready: false, forecast: null });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const { loading, ready, forecast } = state;
  const info = ready ? forecast.info : null;
  const timeline = ready ? forecast.timeline : [];
  const rollout = ready ? forecast.rollout : [];

  return (
    <div className="forecast-view">
      <div className="f-head">
        <div>
          <h2>CyberForeSight</h2>
          <p>AI-based network infiltration forecasting · CIC-IDS-2018</p>
        </div>
        {ready && <span className="f-ready">● LIVE ARTIFACTS</span>}
      </div>

      {loading && <div className="f-empty">Loading forecast artifacts…</div>}

      {!loading && !ready && (
        <div className="f-card f-error">
          <h3>Pipeline artifacts not found</h3>
          <p>
            The forecast dashboard reads the model outputs in <code>models/</code>. Generate them from the
            project root, then refresh this page:
          </p>
          <pre className="f-cmd">
            .venv\Scripts\python run.py --stage features
            .venv\Scripts\python run.py --stage train
            .venv\Scripts\python run.py --stage forecast
            .venv\Scripts\python run.py --stage explain
            .venv\Scripts\python run.py --stage benchmark
          </pre>
        </div>
      )}

      {ready && (
        <>
          <div className="f-kpis">
            <Kpi label="First attack window" value={fmtDate(info.first_attack_ts)} />
            <Kpi label="Earliest pre-attack flag" value={info.earliest_pre_flag_idx === -1 ? "none" : `+${info.lead_minutes} min before`} accent="warn" />
            <Kpi label="Infiltration lead time" value={info.lead_minutes >= 0 ? `${info.lead_minutes} min` : "—"} accent="attack" />
            <Kpi label="Pre-flag windows" value={info.pre_flag_count} />
            <Kpi label="Threat threshold" value={info.threshold} />
            <Kpi label="Rollout horizon" value={`${info.k_steps} min`} />
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
                  <h3>Scenario</h3>
                </div>
                <ul className="f-list">
                  <li>Windows of <b>{info.seq_len}</b> consecutive network states feed the LSTM.</li>
                  <li>The model forecasts next-window attack probability; alerting starts at <b>{num(info.threshold) * 100}%</b>.</li>
                  <li>On this file the model flagged infiltration <b>{info.lead_minutes} minutes</b> before ground truth.</li>
                </ul>
              </div>
            )}
          </div>

          <AttentionPanel attention={forecast.attention} />
          <ShapPanel shap={forecast.shap} />
          <BenchmarkPanel metrics={forecast.benchmarkMetrics} compare={forecast.benchmarkCompare} />
        </>
      )}
    </div>
  );
}