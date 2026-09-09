import { useCallback, useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";
import ForecastDashboard from "./ForecastDashboard.jsx";
import DeviceHistory from "./components/DeviceHistory.jsx";
import JarvisChat from "./components/JarvisChat.jsx";
import "./App.css";

const socket = io("/", {
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 10000,
});

const viewFromPath = (pathname) => {
  if (pathname === "/forecast-view" || pathname === "/forecast") return "forecast";
  if (pathname === "/history") return "history";
  return "live";
};

const pathFromView = (view) => (view === "forecast" ? "/forecast-view" : view === "history" ? "/history" : "/");

function Sparkline({ data = [], color = "#53e3ff", width = 100, height = 24, max = 100 }) {
  if (!data || data.length < 2) {
    return (
      <svg width={width} height={height} className="sparkline-svg">
        <line x1="0" y1={height / 2} x2={width} y2={height / 2} stroke="rgba(255,255,255,0.15)" strokeDasharray="3,3" />
      </svg>
    );
  }
  const pts = data.map((val, idx) => {
    const x = (idx / (data.length - 1)) * width;
    const clamped = Math.max(0, Math.min(max, val));
    const y = height - (clamped / max) * (height - 6) - 3;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const pathData = `M ${pts.join(" L ")}`;
  const lastVal = data[data.length - 1];
  const lastX = width;
  const lastY = height - (Math.max(0, Math.min(max, lastVal)) / max) * (height - 6) - 3;

  return (
    <svg width={width} height={height} className="sparkline-svg" viewBox={`0 0 ${width} ${height}`}>
      <path d={pathData} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={lastX} cy={lastY} r="3" fill={color} />
    </svg>
  );
}

function HardwareInspectorModal({ device, history = [], onClose }) {
  if (!device) return null;
  const cpuHistory = history.map((h) => h.cpu);
  const ramHistory = history.map((h) => h.ram);
  const cpu = device.cpu ?? 0;
  const ram = device.ram ?? 0;

  return (
    <div className="hw-modal-overlay" onClick={onClose}>
      <div className="hw-modal-content glass" onClick={(e) => e.stopPropagation()}>
        <div className="hw-modal-header">
          <div className="hw-modal-title">
            <span className="hw-pulse-live">●</span>
            <h3>{device.name || device.hostname}</h3>
            <span className="hw-tag">
              {device.source === "host-telemetry"
                ? "HOST ENGINE"
                : device.isHotspot
                ? "HOTSPOT NODE"
                : "CONNECTED NODE"}
            </span>
          </div>
          <button className="hw-close-btn" onClick={onClose} aria-label="Close modal">✕</button>
        </div>

        <div className="hw-grid">
          {/* CPU Card */}
          <div className="hw-card">
            <div className="hw-card-head">
              <span className="hw-card-lbl">LIVE CPU UTILIZATION</span>
              <strong className={`hw-pct ${cpu > 80 ? "txt-red" : cpu > 50 ? "txt-amber" : "txt-cyan"}`}>
                {cpu}%
              </strong>
            </div>
            <div className="hw-bar-track lg">
              <div
                className={`hw-bar-fill ${cpu > 80 ? "crit" : cpu > 50 ? "warn" : "norm"}`}
                style={{ width: `${Math.min(100, Math.max(3, cpu))}%` }}
              />
            </div>
            <div className="hw-sparkline-row">
              <span className="hw-sub-lbl">Rolling 30s Trend:</span>
              <Sparkline
                data={cpuHistory}
                color={cpu > 80 ? "#ff4d6d" : cpu > 50 ? "#ffb703" : "#53e3ff"}
                width={160}
                height={32}
              />
            </div>
            <div className="hw-card-footer">
              <span>Logical Cores: <strong>{device.cores || "--"}</strong></span>
              <span>Status: <strong className="green">ONLINE</strong></span>
            </div>
          </div>

          {/* RAM Card */}
          <div className="hw-card">
            <div className="hw-card-head">
              <span className="hw-card-lbl">LIVE MEMORY (RAM)</span>
              <strong className={`hw-pct ${ram > 80 ? "txt-red" : ram > 50 ? "txt-amber" : "txt-cyan"}`}>
                {ram}%
              </strong>
            </div>
            <div className="hw-bar-track lg">
              <div
                className={`hw-bar-fill ram ${ram > 80 ? "crit" : ram > 50 ? "warn" : "norm"}`}
                style={{ width: `${Math.min(100, Math.max(3, ram))}%` }}
              />
            </div>
            <div className="hw-sparkline-row">
              <span className="hw-sub-lbl">Rolling 30s Trend:</span>
              <Sparkline
                data={ramHistory}
                color={ram > 80 ? "#ff4d6d" : ram > 50 ? "#ffb703" : "#a78bfa"}
                width={160}
                height={32}
              />
            </div>
            <div className="hw-card-footer">
              <span>Memory In Use: <strong>{device.ramUsedGb ? `${device.ramUsedGb} GB` : "--"} {device.ramGb ? `/ ${device.ramGb} GB` : ""}</strong></span>
              <span>Load: <strong className={ram > 80 ? "txt-red" : "txt-cyan"}>{ram > 80 ? "HIGH" : "NORMAL"}</strong></span>
            </div>
          </div>
        </div>

        {/* System & Network Specifications */}
        <div className="hw-meta-card">
          <div className="hw-meta-grid">
            <div className="hw-meta-item">
              <span className="meta-lbl">IP ADDRESS</span>
              <strong>{device.ip || "127.0.0.1"}</strong>
            </div>
            <div className="hw-meta-item">
              <span className="meta-lbl">MAC ADDRESS</span>
              <strong>{device.mac || "Virtual / Host Loopback"}</strong>
            </div>
            <div className="hw-meta-item">
              <span className="meta-lbl">OPERATING SYSTEM</span>
              <strong>{device.os || "Unknown"}</strong>
            </div>
            <div className="hw-meta-item">
              <span className="meta-lbl">TELEMETRY CHANNEL</span>
              <strong>{device.source || "Socket.IO Live Stream"}</strong>
            </div>
          </div>
        </div>

        {/* Instruction if CPU is 0 from pure ARP */}
        {cpu === 0 && ram === 0 && device.source !== "host-telemetry" && (
          <div className="hw-agent-hint">
            <p>💡 <em>This node was discovered via network scan. To stream 100% live hardware load from this machine, run:</em></p>
            <code>python collectors/client_agent.py http://192.168.137.1:5000</code>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [currentView, setCurrentView] = useState(() => viewFromPath(window.location.pathname));
  const [connectionStatus, setConnectionStatus] = useState(() =>
    socket.connected ? "ONLINE" : "RECONNECTING"
  ); // 'ONLINE' | 'RECONNECTING' | 'OFFLINE'
  const [devices, setDevices] = useState([]);
  const [events, setEvents] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [deviceName, setDeviceName] = useState(() => localStorage.getItem("deviceName") || "");
  const [hardwareHistory, setHardwareHistory] = useState({});
  const [selectedDevice, setSelectedDevice] = useState(null);

  const pushHardwareSample = useCallback((dev) => {
    if (!dev || !dev.hostname) return;
    setHardwareHistory((prev) => {
      const list = prev[dev.hostname] || [];
      const updated = [...list, { time: Date.now(), cpu: dev.cpu || 0, ram: dev.ram || 0 }].slice(-20);
      return { ...prev, [dev.hostname]: updated };
    });
  }, []);

  const appShellRef = useRef(null);

  useEffect(() => {
    appShellRef.current?.scrollTo({ top: 0, left: 0 });
  }, [currentView]);

  useEffect(() => {
    const handlePopState = () => setCurrentView(viewFromPath(window.location.pathname));
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigateToView = (view) => {
    const path = pathFromView(view);
    if (window.location.pathname !== path) {
      window.history.pushState({}, "", path);
    }
    setCurrentView(view);
  };

  // Parent-level chat history (persists across tab switches)
  const [chatMessages, setChatMessages] = useState([
    {
      id: "init",
      role: "assistant",
      content: "Systems online. How can I help?",
      timestamp: new Date().toLocaleTimeString([], {
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
      }),
      type: "chat",
      spoken: true,
    },
  ]);

  const lastResponseRef = useRef("");

  useEffect(() => {
    const onConnect = () => {
      setConnectionStatus("ONLINE");
    };

    const onDisconnect = (reason) => {
      setConnectionStatus(reason === "io client disconnect" ? "OFFLINE" : "RECONNECTING");
    };

    const onConnectError = () => {
      setConnectionStatus("OFFLINE");
    };

    const onReconnectAttempt = () => {
      setConnectionStatus("RECONNECTING");
    };

    const onReconnect = () => {
      setConnectionStatus("ONLINE");
    };

    const onWorldUpdate = (world) => {
      const list = Object.values(world.devices || {});
      setDevices(list);
      setEvents((world.recentEvents || []).slice().reverse());
      list.forEach(pushHardwareSample);
    };

    const onDeviceUpdate = (device) => {
      setDevices((prev) => [
        ...prev.filter((d) => d.hostname !== device.hostname),
        device,
      ]);
      pushHardwareSample(device);
      setSelectedDevice((current) => (current && current.hostname === device.hostname ? device : current));
    };

    const onJarvisIntelligence = (data) => {
      const response =
        data?.jarvis_report ||
        data?.report ||
        data?.response ||
        (typeof data === "string" ? data : JSON.stringify(data));

      if (!response) return;

      // Deduplication: do not append if identical to recent response
      if (response === lastResponseRef.current) return;
      lastResponseRef.current = response;

      setChatMessages((prev) => [
        ...prev,
        {
          id: "intel_" + Date.now() + "_" + Math.random().toString(36).substring(2, 6),
          role: "assistant",
          content: response,
          timestamp: new Date().toLocaleTimeString([], {
            hour12: false,
            hour: "2-digit",
            minute: "2-digit",
          }),
          type: "intelligence",
          spoken: false,
        },
      ]);
    };

    // Socket.IO lifecycle listeners
    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("connect_error", onConnectError);
    socket.io.on("reconnect_attempt", onReconnectAttempt);
    socket.io.on("reconnect", onReconnect);

    socket.on("world_update", onWorldUpdate);
    socket.on("device_update", onDeviceUpdate);
    socket.on("jarvis_intelligence", onJarvisIntelligence);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("connect_error", onConnectError);
      socket.io.off("reconnect_attempt", onReconnectAttempt);
      socket.io.off("reconnect", onReconnect);
      socket.off("world_update", onWorldUpdate);
      socket.off("device_update", onDeviceUpdate);
      socket.off("jarvis_intelligence", onJarvisIntelligence);
    };
  }, []);

  const postDevice = useCallback(async (name) => {
    const clientId = sessionStorage.getItem("clientId") || "Client-x";
    try {
      await fetch("/device", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          hostname: clientId,
          name: name || localStorage.getItem("deviceName") || "",
          os: navigator.platform || "Web",
          cpu: navigator.hardwareConcurrency || 0,
          ram: navigator.deviceMemory || 0,
          status: "online",
        }),
      });
    } catch {
      // backend unreachable — retry on next heartbeat
    }
  }, []);

  const saveDeviceName = () => {
    const name = deviceName.trim();
    localStorage.setItem("deviceName", name);
    postDevice(name);
  };

  useEffect(() => {
    let clientId = sessionStorage.getItem("clientId");

    if (!clientId) {
      clientId = "Client-" + Math.random().toString(36).slice(2, 6);
      sessionStorage.setItem("clientId", clientId);
    }

    // Mobile browsers freeze timers when a tab is backgrounded/screen locked,
    // killing heartbeats and sockets. Resync the instant the tab is visible.
    const resync = () => {
      if (document.visibilityState !== "visible") return;
      if (!socket.connected) socket.connect();
      postDevice();
    };

    document.addEventListener("visibilitychange", resync);

    postDevice();
    const heartbeat = setInterval(() => postDevice(), 8000);

    return () => {
      document.removeEventListener("visibilitychange", resync);
      clearInterval(heartbeat);
    };
  }, [postDevice]);

  const handleSendMessage = async (command) => {
    if (!command.trim() || isProcessing) return;

    const time = new Date().toLocaleTimeString([], {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
    });

    const userMsg = {
      id: "user_" + Date.now(),
      role: "user",
      content: command,
      timestamp: time,
      type: "chat",
    };

    setChatMessages((prev) => [...prev, userMsg]);
    setIsProcessing(true);

    try {
      const response = await fetch("/voice-command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with HTTP ${response.status}`);
      }

      const data = await response.json();
      const result =
        data?.result?.response ||
        data?.result?.jarvis_report ||
        data?.result?.report ||
        data?.response ||
        "I could not process that command.";

      lastResponseRef.current = result;

      const assistantMsg = {
        id: "asst_" + Date.now(),
        role: "assistant",
        content: result,
        timestamp: new Date().toLocaleTimeString([], {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
        }),
        type: "chat",
        spoken: false,
      };

      setChatMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          id: "err_" + Date.now(),
          role: "assistant",
          content: "Connection unavailable. Backend service is offline.",
          timestamp: new Date().toLocaleTimeString([], {
            hour12: false,
            hour: "2-digit",
            minute: "2-digit",
          }),
          type: "error",
          spoken: false,
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const getThreat = (device) => {
    const matching = events.filter(
      (e) => e.device === device.hostname || e.device === device.ip
    );

    if (!matching.length) return "normal";

    const risk = Math.max(...matching.map((e) => Number(e.risk || 0)));

    if (risk >= 80) return "critical";
    if (risk >= 60) return "high";
    if (risk >= 30) return "medium";

    return "normal";
  };

  const highestThreat = () => {
    if (!devices.length) return "NOMINAL";
    const threats = devices.map((d) => getThreat(d));
    if (threats.includes("critical")) return "CRITICAL";
    if (threats.includes("high")) return "HIGH";
    if (threats.includes("medium")) return "ELEVATED";
    return "NOMINAL";
  };

  const radarPosition = (index, total) => {
    const angle = (index / Math.max(total, 1)) * Math.PI * 2 - Math.PI / 2;
    const radii = [42, 68, 54, 76, 62, 48, 70];
    const r = radii[index % radii.length];

    return {
      left: `${50 + Math.cos(angle) * (r / 2)}%`,
      top: `${50 + Math.sin(angle) * (r / 2)}%`,
    };
  };

  return (
    <div ref={appShellRef} className="jarvis">
      {/* HEADER */}
      <header className="header">
        <div className="logo-area">
          <div className="logo-orb">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 2.5 4 5.5v6c0 4.6 3.4 8.4 8 10 4.6-1.6 8-5.4 8-10v-6l-8-3Z" />
              <path d="M8.4 12.1 11 14.7l4.7-5.2" />
              <circle cx="12" cy="21" r="0.5" fill="currentColor" />
            </svg>
          </div>

          <div>
            <h1>CYBERFORESIGHT</h1>
            <p className="brand-sub">AI Temporal World Model · <b>SIH-26153</b></p>
          </div>
        </div>

        <div className="header-right">
          <div className="network-pill" title="Live Server Network">
            <span className="dot"></span>
            <span>LAN: 172.100.128.62</span>
          </div>

          <div
            className={`online-status-badge ${
              connectionStatus === "ONLINE"
                ? "status-online"
                : connectionStatus === "RECONNECTING"
                ? "status-reconnecting"
                : "status-offline"
            }`}
            role="status"
            aria-live="polite"
          >
            <span className="status-dot">●</span>
            {connectionStatus === "ONLINE"
              ? "SYSTEM ONLINE"
              : connectionStatus === "RECONNECTING"
              ? "SYSTEM RECONNECTING"
              : "SYSTEM OFFLINE"}
          </div>

          {/* 3-WAY NAVIGATION */}
          <nav className="view-toggle" role="group" aria-label="Dashboard Views">
            <button
              type="button"
              className={currentView === "live" ? "active" : ""}
              onClick={() => navigateToView("live")}
              aria-pressed={currentView === "live"}
            >
              🌐 Threat Radar
            </button>
            <button
              type="button"
              className={currentView === "forecast" ? "active" : ""}
              onClick={() => navigateToView("forecast")}
              aria-pressed={currentView === "forecast"}
            >
              🔮 Threat Forecast
            </button>
            <button
              type="button"
              className={currentView === "history" ? "active" : ""}
              onClick={() => navigateToView("history")}
              aria-pressed={currentView === "history"}
            >
              📜 Device History
            </button>
          </nav>
        </div>
      </header>

      {/* VIEW SWITCHER */}
      {currentView === "forecast" ? (
        <ForecastDashboard />
      ) : currentView === "history" ? (
        <DeviceHistory socket={socket} />
      ) : (
        <main className="main-grid">
          {/* 1. LEFT: NETWORK THREAT RADAR HERO */}
          <div className="radar-column">
            <section className="glass radar-section" aria-label="Network Threat Radar">
              <div className="section-head">
                <div className="radar-head-title">
                  <span className="radar-pulse-dot">●</span>
                  <span>NETWORK THREAT RADAR</span>
                </div>
                <span className="live">● 360° ACTIVE SWEEP</span>
              </div>

              <div className="radar-scope-container">
                <div className="radar">
                  {/* Concentric distance rings */}
                  <div className="radar-outer-ring"></div>
                  <div className="ring r3">
                  </div>
                  <div className="ring r2">
                  </div>
                  <div className="ring r1">
                  </div>

                  {/* Crosshair reticle lines */}
                  <div className="cross x"></div>
                  <div className="cross y"></div>
                  <div className="cross diag-1"></div>
                  <div className="cross diag-2"></div>

                  {/* Sonar ping echo wave */}
                  <div className="sonar-ping"></div>

                  {/* 360-degree rotating sweep beam */}
                  <div className="sweep"></div>

                  {/* Center JARVIS core */}
                  <div className="radar-core">
                    <div className="core">J</div>
                    <span>JARVIS</span>
                  </div>

                  {/* Dynamic threat nodes */}
                  {devices.map((device, index) => {
                    const threat = getThreat(device);
                    return (
                      <div
                        key={device.hostname}
                        className={`radar-node ${threat}`}
                        style={radarPosition(index, devices.length)}
                        title={`${device.name || device.ip} (${device.ip || "local"}) - Threat: ${threat}`}
                      >
                        <div className="node-ping"></div>
                        <div className="node-dot"></div>
                        <span className="node-tag">{device.name || device.ip}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Radar HUD telemetry & status */}
              <div className="radar-hud-footer">
                <div className="radar-hud-grid">
                  <div className="hud-metric">
                    <span className="hud-lbl">TARGETS DETECTED</span>
                    <strong className="hud-val cyan">{devices.length} HOSTS</strong>
                  </div>
                  <div className="hud-metric">
                    <span className="hud-lbl">THREAT STATUS</span>
                    <strong className={`hud-val threat-${highestThreat().toLowerCase()}`}>
                      {highestThreat()}
                    </strong>
                  </div>
                  <div className="hud-metric">
                    <span className="hud-lbl">SCAN CARRIER</span>
                    <strong className="hud-val">2.4 GHz / 360°</strong>
                  </div>
                  <div className="hud-metric">
                    <span className="hud-lbl">DEFENSE SHIELD</span>
                    <strong className="hud-val green">ARMED & ACTIVE</strong>
                  </div>
                </div>
                <div className="radar-hud-sub">
                  <span>● AI WORLD MODEL CORRELATED · 60S SLIDING WINDOW</span>
                </div>
              </div>
            </section>
          </div>

          {/* 2. CENTER: PROMINENT JARVIS CHAT CONSOLE */}
          <div className="chat-center-column">
            <JarvisChat
              messages={chatMessages}
              onSendMessage={handleSendMessage}
              isProcessing={isProcessing}
              connectionStatus={connectionStatus}
            />
          </div>

          {/* 3. RIGHT: CONNECTED DEVICES & RECENT SECURITY INTELLIGENCE */}
          <div className="telemetry-column">
            {/* CONNECTED DEVICES */}
            <section className="glass devices" aria-label="Connected Devices">
              <div className="section-head">
                <div className="sec-head-left">
                  <span className="sec-dot">●</span>
                  <span>CONNECTED DEVICES</span>
                </div>
                <span className="device-count-badge">{devices.length} ACTIVE</span>
              </div>

              <div className="name-this">
                <input
                  type="text"
                  placeholder="Name this device"
                  value={deviceName}
                  maxLength={40}
                  onChange={(e) => setDeviceName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && saveDeviceName()}
                />
                <button onClick={saveDeviceName}>SAVE</button>
              </div>

              <div className="device-list">
                {devices.length === 0 ? (
                  <div className="no-devices">Waiting for devices...</div>
                ) : (
                  devices.map((device) => {
                    const threat = getThreat(device);
                    const history = hardwareHistory[device.hostname] || [];
                    const cpuHistory = history.map((h) => h.cpu);
                    const cpu = device.cpu ?? 0;
                    const ram = device.ram ?? 0;

                    return (
                      <div
                        className={`device live-device-card ${threat}`}
                        key={device.hostname}
                        data-level={threat}
                        onClick={() => setSelectedDevice(device)}
                        role="button"
                        tabIndex={0}
                        title="Click to inspect live hardware telemetry"
                      >
                        <div className="device-circle">
                          {threat === "critical"
                            ? "⚠️"
                            : device.source === "host-telemetry"
                            ? "🖥️"
                            : "💻"}
                        </div>
                        <div className="device-data">
                          <div className="device-title-row">
                            <strong>{device.name || device.ip}</strong>
                            <span className={`threat-pill ${threat}`}>{threat.toUpperCase()}</span>
                          </div>
                          <div className="device-sub-row">
                            <small className="device-ip">{device.ip || "127.0.0.1"}</small>
                            <span className="live-pulse-badge">
                              <span className="live-dot-pulse">●</span> LIVE
                            </span>
                          </div>

                          {/* Live Dynamic Hardware Meters */}
                          <div className="device-hw-meters">
                            <div className="hw-meter-item">
                              <div className="hw-meter-label">
                                <span>CPU</span>
                                <strong className={cpu > 80 ? "txt-red" : cpu > 50 ? "txt-amber" : "txt-cyan"}>
                                  {cpu}%
                                </strong>
                              </div>
                              <div className="hw-bar-track">
                                <div
                                  className={`hw-bar-fill ${cpu > 80 ? "crit" : cpu > 50 ? "warn" : "norm"}`}
                                  style={{ width: `${Math.min(100, Math.max(4, cpu))}%` }}
                                />
                              </div>
                            </div>

                            <div className="hw-meter-item">
                              <div className="hw-meter-label">
                                <span>RAM</span>
                                <strong className={ram > 80 ? "txt-red" : ram > 50 ? "txt-amber" : "txt-cyan"}>
                                  {ram}%
                                </strong>
                              </div>
                              <div className="hw-bar-track">
                                <div
                                  className={`hw-bar-fill ram ${ram > 80 ? "crit" : ram > 50 ? "warn" : "norm"}`}
                                  style={{ width: `${Math.min(100, Math.max(4, ram))}%` }}
                                />
                              </div>
                            </div>
                          </div>

                          {/* Mini Sparkline Trend */}
                          {cpuHistory.length > 2 && (
                            <div className="device-sparkline-preview">
                              <Sparkline
                                data={cpuHistory}
                                color={cpu > 80 ? "#ff4d6d" : cpu > 50 ? "#ffb703" : "#53e3ff"}
                                width={120}
                                height={18}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </section>

            {/* RECENT SECURITY EVENTS */}
            <section className="glass events-section" aria-label="Recent Security Events">
              <div className="section-head">
                <div className="sec-head-left">
                  <span className="sec-dot amber">●</span>
                  <span>RECENT SECURITY INTELLIGENCE</span>
                </div>
                <span className="live">{events.length} EVENTS</span>
              </div>

              <div className="events-list">
                {events.length === 0 ? (
                  <div className="no-devices">No security events logged</div>
                ) : (
                  events.slice(0, 15).map((evt, idx) => (
                    <div className="event-item" key={idx}>
                      <div className="event-time">
                        {evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString([], { hour12: false }) : "—"}
                      </div>
                      <div className="event-body">
                        <strong>{evt.device || "Network"}</strong>
                        <span>{evt.attack || evt.message || "Security telemetry update"}</span>
                      </div>
                      <span className={`event-level level-${String(evt.level || "info").toLowerCase()}`}>
                        {evt.level || "INFO"}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>
        </main>
      )}

      {/* LIVE HARDWARE INSPECTOR MODAL */}
      {selectedDevice && (
        <HardwareInspectorModal
          device={selectedDevice}
          history={hardwareHistory[selectedDevice.hostname] || []}
          onClose={() => setSelectedDevice(null)}
        />
      )}
    </div>
  );
}
