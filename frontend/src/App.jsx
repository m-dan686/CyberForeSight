import { useEffect, useRef, useState } from "react";
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

export default function App() {
  const [currentView, setCurrentView] = useState("live"); // 'live' | 'forecast' | 'history'
  const [connectionStatus, setConnectionStatus] = useState(() =>
    socket.connected ? "ONLINE" : "RECONNECTING"
  ); // 'ONLINE' | 'RECONNECTING' | 'OFFLINE'
  const [devices, setDevices] = useState([]);
  const [events, setEvents] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [deviceNameInput, setDeviceNameInput] = useState(
    () => localStorage.getItem("deviceName") || ""
  );

  const registerRef = useRef(null);

  const saveDeviceName = () => {
    const value = deviceNameInput.trim();
    localStorage.setItem("deviceName", value);
    registerRef.current?.();
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
      setDevices(Object.values(world.devices || {}));
      setEvents((world.recentEvents || []).slice().reverse());
    };

    const onDeviceUpdate = (device) => {
      setDevices((prev) => [
        ...prev.filter((d) => d.hostname !== device.hostname),
        device,
      ]);
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

  useEffect(() => {
    let clientId = sessionStorage.getItem("clientId");

    if (!clientId) {
      clientId = "Client-" + Math.random().toString(36).slice(2, 6);
      sessionStorage.setItem("clientId", clientId);
    }

    const register = async () => {
      try {
        await fetch("/device", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            hostname: clientId,
            name: localStorage.getItem("deviceName") || "",
            os: navigator.platform || "Web",
            cpu: navigator.hardwareConcurrency || 0,
            ram: navigator.deviceMemory || 0,
            status: "online",
          }),
        });
      } catch {
        // backend unreachable — retry on next heartbeat
      }
    };

    registerRef.current = register;

    register();
    const heartbeat = setInterval(register, 8000);

    return () => clearInterval(heartbeat);
  }, []);

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
    <div className="jarvis">
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
              onClick={() => setCurrentView("live")}
              aria-pressed={currentView === "live"}
            >
              🌐 Threat Radar
            </button>
            <button
              type="button"
              className={currentView === "forecast" ? "active" : ""}
              onClick={() => setCurrentView("forecast")}
              aria-pressed={currentView === "forecast"}
            >
              🔮 Forecast Lab
            </button>
            <button
              type="button"
              className={currentView === "history" ? "active" : ""}
              onClick={() => setCurrentView("history")}
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
                <div className="radar-hud-azimuth">
                  <span className="azimuth-mark az-n">000° N</span>
                  <span className="azimuth-mark az-e">090° E</span>
                  <span className="azimuth-mark az-s">180° S</span>
                  <span className="azimuth-mark az-w">270° W</span>
                </div>

                <div className="radar">
                  {/* Concentric distance rings */}
                  <div className="radar-outer-ring"></div>
                  <div className="ring r3">
                    <span className="ring-label">ZONE 3 · PERIMETER</span>
                  </div>
                  <div className="ring r2">
                    <span className="ring-label">ZONE 2 · SUBNET</span>
                  </div>
                  <div className="ring r1">
                    <span className="ring-label">ZONE 1 · CORE</span>
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
                        title={`${device.name || device.hostname} (${device.ip || "local"}) - Threat: ${threat}`}
                      >
                        <div className="node-ping"></div>
                        <div className="node-dot"></div>
                        <span className="node-tag">{device.name || device.hostname}</span>
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
                  value={deviceNameInput}
                  onChange={(e) => setDeviceNameInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") saveDeviceName();
                  }}
                  placeholder="Label this terminal (e.g., SOC-1)..."
                  aria-label="Name this device"
                />
                <button onClick={saveDeviceName}>Set</button>
              </div>

              <div className="device-list">
                {devices.length === 0 ? (
                  <div className="no-devices">Waiting for devices...</div>
                ) : (
                  devices.map((device) => {
                    const threat = getThreat(device);
                    return (
                      <div className="device" key={device.hostname} data-level={threat}>
                        <div className="device-circle">
                          {threat === "critical" ? "⚠️" : "💻"}
                        </div>
                        <div className="device-data">
                          <div className="device-title-row">
                            <strong>{device.name || device.hostname}</strong>
                            <span className={`threat-pill ${threat}`}>{threat.toUpperCase()}</span>
                          </div>
                          <small className="device-ip">{device.ip || "127.0.0.1"}</small>
                          <small className="device-specs">
                            CPU {device.cpu ?? "--"}% &nbsp; RAM {device.ram ?? "--"}%
                          </small>
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
    </div>
  );
}