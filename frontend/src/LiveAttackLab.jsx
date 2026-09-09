import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";

const API = "";
const socket = io("/");

const PHASE_META = {
  idle: { label: "BASELINE", cls: "idle" },
  ramp: { label: "RAMPS UP", cls: "ramp" },
  attack: { label: "ATTACK LANDED", cls: "attack" },
};

function LiveSpark({ series, threshold }) {
  const W = 920;
  const H = 120;
  const PAD = { l: 42, r: 12, t: 10, b: 22 };
  const n = series.length;
  if (n < 2) {
    return <div className="f-empty">waiting for live windows…</div>;
  }
  const x = (i) => PAD.l + (i / (n - 1)) * (W - PAD.l - PAD.r);
  const y = (p) => PAD.t + (1 - p) * (H - PAD.t - PAD.b);
  const line = series.map((s, i) => `${x(i).toFixed(1)},${y(s.p).toFixed(1)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="f-chart f-lab-chart" role="img" aria-label="live attack probability">
      <defs>
        <linearGradient id="labFill" x1="0" y1="0" x2="0" y2="1">
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
      <polygon points={`${PAD.l},${y(0)} ${line} ${x(n - 1)},${y(0)}`} fill="url(#labFill)" />
      <polyline points={line} fill="none" stroke="#37bee6" strokeWidth="2.2" />
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

function RolloutBars({ rows, threshold }) {
  if (!rows || rows.length === 0) return <div className="f-sub">no rollout (baseline windows hold steady)</div>;
  const W = 920;
  const H = 110;
  const slot = W / rows.length;
  const maxProb = 1;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="f-chart" role="img" aria-label="live k-step forecast">
      {rows.map((r, i) => {
        const h = (r.prob / maxProb) * (H - 26);
        const over = r.prob >= threshold;
        return (
          <g key={i}>
            <rect
              x={i * slot + 6}
              y={H - 22 - h}
              width={slot - 12}
              height={Math.max(h, 1)}
              fill={over ? "#ff4d6d" : "#f59e0b"}
              rx="2"
            />
            <text x={i * slot + slot / 2} y={H - 22 - h - 5} textAnchor="middle" className="f-axis" fontSize="10">
              {r.prob.toFixed(2)}
            </text>
            <text x={i * slot + slot / 2} y={H - 6} textAnchor="middle" className="f-axis" fontSize="10">
              {r.stage}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function LiveAttackLab() {
  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState("idle");
  const [last, setLast] = useState(null);
  const [series, setSeries] = useState([]);
  const [log, setLog] = useState(["Ready. Start the live feed to watch the model react to real Infiltration traffic."]);
  const [speed, setSpeed] = useState(1.0);
  const [busy, setBusy] = useState(false);
  const firstFlagRef = useRef(null);
  const leadRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/live-sim/state`)
      .then((r) => r.json())
      .then((s) => {
        if (s?.running && s.last) {
          setRunning(true);
          setPhase(s.last.phase || "idle");
          setLast(s.last);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const onState = (m) => {
      setLast(m);
      setPhase(m.phase);
      setSeries((prev) => [...prev.slice(-149), { w: m.window_start, p: m.prob }]);

      if (m.phase === "ramp" && m.flag && !firstFlagRef.current) {
        firstFlagRef.current = m;
        setLog((prev) => [...prev.slice(-7), `⚠️ Forecast flagged infiltration ${m.window_start.slice(11)} (P=${m.prob.toFixed(2)}) — before the simulated attack lands`]);
      }
      if (m.phase === "attack" && firstFlagRef.current && !leadRef.current) {
        const t0 = new Date(firstFlagRef.current.window_start.replace(" ", "T"));
        const onset = new Date(m.window_start.replace(" ", "T"));
        const mins = Math.round((onset - t0) / 60000);
        leadRef.current = mins;
        setLog((prev) => [...prev.slice(-7), `Simulated infiltration landed 02:00. Forecast lead observed: ${mins} minutes ahead.`]);
      }
    };
    const onCtrl = (m) => {
      if (m.type === "ready") {
        setRunning(true);
        setLog((prev) => [...prev.slice(-7), "✓ Live feed ready — replayed CIC-IDS2018 states through the trained world model"]);
      } else if (m.type === "stopped") {
        setRunning(false);
        setLog((prev) => [...prev.slice(-7), "Feed stopped."]);
      } else if (m.cmd === "trigger") {
        if (m.skipped) return;
        setLog((prev) => [...prev.slice(-7), "★ Dummy attack injected — replaying the real infiltration ramp (01:47→02:00), then the onset burst"]);
      } else if (m.cmd === "return-to-baseline") {
        setLog((prev) => [...prev.slice(-7), "Attack cycle complete — network returned to baseline traffic."]);
      } else if (m.cmd === "reset") {
        setLog((prev) => [...prev.slice(-7), "Reset to baseline."]);
      }
    };
    const onError = (m) => setLog((prev) => [...prev.slice(-7), `⚠ ${m.error}`]);

    socket.on("live_sim_state", onState);
    socket.on("live_sim_ctrl", onCtrl);
    socket.on("live_sim_error", onError);
    return () => {
      socket.off("live_sim_state", onState);
      socket.off("live_sim_ctrl", onCtrl);
      socket.off("live_sim_error", onError);
    };
  }, []);

  const post = async (path, body) => {
    setBusy(true);
    try {
      const res = await fetch(`${API}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {}),
      });
      const data = await res.json();
      if (!data.success) setLog((prev) => [...prev.slice(-7), `⚠ ${data.error || "request failed"}`]);
      return data;
    } catch {
      setLog((prev) => [...prev.slice(-7), "⚠ Cannot reach backend"]);
    } finally {
      setBusy(false);
    }
    return null;
  };

  const start = async () => {
    leadRef.current = null;
    firstFlagRef.current = null;
    setSeries([]);
    setLog((prev) => [...prev.slice(-7), "Starting live feed… (Δ1s = 1 simulated minute)"]);
    await post("/live-sim/start", { tick: speed });
  };

  const trigger = () => post("/live-sim/command", { cmd: "trigger" });
  const reset = () => {
    leadRef.current = null;
    firstFlagRef.current = null;
    setSeries([]);
    post("/live-sim/command", { cmd: "reset" });
  };
  const stop = () => post("/live-sim/stop");

  const phaseMeta = PHASE_META[phase] || PHASE_META.idle;
  const pct = last ? (last.prob * 100).toFixed(1) : "—";
  const leadText = last && last.window_start;

  return (
    <div className="f-card f-lab">
      <div className="f-card-head">
        <div className="f-lab-title">
          <h3>Live Attack Lab — watch the forecast move</h3>
          <span className="f-badge">simulated infiltration · real model forward passes</span>
        </div>
        <div className="f-lab-ctrls">
          {!running && (
            <button className="f-btn" onClick={start} disabled={busy}>
              ▶ Start live feed
            </button>
          )}
          {running && (
            <>
              <button className="f-btn" onClick={stop} disabled={busy}>
                ■ Stop
              </button>
              <button className="f-btn f-btn-warn" onClick={reset} disabled={busy}>
                ⟲ Reset
              </button>
            </>
          )}
        </div>
      </div>

      <div className="f-lab-row">
        <div className={`f-lab-phase ph-${phaseMeta.cls}`}>{phaseMeta.label}</div>
        <div className="f-lab-prob">
          <span>P(attack)</span>
          <strong>{pct}%</strong>
        </div>
        <div className="f-lab-cell">
          <span>Simulated traffic</span>
          <b>{last ? leadText : "no windows yet"}</b>
        </div>
        <div className="f-lab-cell">
          <span>Flag</span>
          <b className={last?.flag ? "txt-attack" : "txt-ok"}>{last ? (last.flag ? "ALERT" : "normal") : "—"}</b>
        </div>
        <div className="f-lab-cell">
          <span>Stage</span>
          <b>{last ? `${last.stage} · ${Math.round((last.stage_confidence || 0) * 100)}%` : "—"}</b>
        </div>
        <label className="f-lab-speed">
          <span>speed</span>
          <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
            <option value={0.25}>0.25s</option>
            <option value={0.5}>0.5s</option>
            <option value={1.0}>1.0s</option>
            <option value={2.0}>2.0s</option>
          </select>
        </label>
      </div>

      {(running || series.length > 0) && (
        <>
          <button
            className="f-btn f-btn-danger f-lab-trigger"
            onClick={trigger}
            disabled={busy}
            title="Inject the simulated infiltration ramp + onset burst"
          >
            ☠ Inject dummy attack
          </button>
          <LiveSpark series={series} threshold={last?.threshold || 0.6} />
          <div className="f-lab-sub">
            <span>K-step live forecast (autoregressive rollout)</span>
            {last?.phase !== "idle" && <span className="f-badge">technique: {last?.stage_technique || "—"}</span>}
          </div>
          <RolloutBars rows={last?.rollout} threshold={last?.threshold || 0.6} />
        </>
      )}

      <div className="f-lab-log">
        {log.map((line, i) => (
          <div className="f-lab-log-line" key={i}>
            {line}
          </div>
        ))}
      </div>
    </div>
  );
}