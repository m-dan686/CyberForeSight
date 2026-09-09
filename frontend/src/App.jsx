import { useEffect, useRef, useState } from "react";
import { io } from "socket.io-client";
import ForecastDashboard from "./ForecastDashboard.jsx";
import DeviceHistory from "./components/DeviceHistory.jsx";
import JarvisChat from "./components/JarvisChat.jsx";
import "./App.css";

const BACKEND_URL = "http://localhost:5000";
const socket = io(BACKEND_URL, {
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

  // Parent-level chat history (persists across tab switches - Rule 44)
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

      // Deduplication: do not append if identical to recent response (Rule 7)
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

    // Socket.IO lifecycle listeners (Rule 12, 35, 36)
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
      const response = await fetch(`${BACKEND_URL}/voice-command`, {
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
      // Truthful error handling (Rule 6: "Connection unavailable. Backend service is offline.")
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

  const radarPosition = (index, total) => {
    const angle = (index / Math.max(total, 1)) * Math.PI * 2;
    const radius = 37;

    return {
      left: `${50 + Math.cos(angle) * radius}%`,
      top: `${50 + Math.sin(angle) * radius}%`,
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
            <p className="brand-sub">
              AI infiltration forecasting · <b>JARVIS</b> core
            </p>
          </div>
        </div>

        <div className="header-right">
          {/* TRUTHFUL SYSTEM STATUS (Rule 12) */}
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

          {/* 3-WAY NAVIGATION (Rule 21, 42, 43) */}
          <nav className="view-toggle" role="group" aria-label="Dashboard Views">
            <button
              type="button"
              className={currentView === "live" ? "active" : ""}
              onClick={() => setCurrentView("live")}
              aria-pressed={currentView === "live"}
            >
              LIVE
            </button>
            <button
              type="button"
              className={currentView === "forecast" ? "active" : ""}
              onClick={() => setCurrentView("forecast")}
              aria-pressed={currentView === "forecast"}
            >
              FORECAST
            </button>
            <button
              type="button"
              className={currentView === "history" ? "active" : ""}
              onClick={() => setCurrentView("history")}
              aria-pressed={currentView === "history"}
            >
              DEVICE HISTORY
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
          {/* LEFT TELEMETRY COLUMN */}
          <div className="left-column">
            {/* CONNECTED DEVICES (Rule 14: Active telemetry only) */}
            <section className="glass devices" aria-label="Connected Devices">
              <div className="section-head">
                <span>CONNECTED DEVICES</span>
                <span className="device-count-badge">{devices.length}</span>
              </div>

              <div className="device-list">
                {devices.length === 0 ? (
                  <div className="no-devices">Waiting for devices...</div>
                ) : (
                  devices.map((device) => {
                    const threat = getThreat(device);
                    return (
                      <div className="device" key={device.hostname} data-level={threat}>
                        <div className="device-circle">●</div>
                        <div className="device-data">
                          <strong>{device.hostname}</strong>
                          <small>{device.ip}</small>
                          <small>
                            CPU {device.cpu ?? "--"}% &nbsp; RAM {device.ram ?? "--"}%
                          </small>
                        </div>
                        <span className={`threat ${threat}`}>{threat}</span>
                      </div>
                    );
                  })
                )}
              </div>
            </section>

            {/* RADAR */}
            <section className="glass radar-section" aria-label="Network Threat Radar">
              <div className="section-head">
                <span>NETWORK THREAT RADAR</span>
                <span className="live">● LIVE</span>
              </div>

              <div className="radar">
                <div className="radar-grid"></div>
                <div className="ring r1"></div>
                <div className="ring r2"></div>
                <div className="ring r3"></div>
                <div className="cross x"></div>
                <div className="cross y"></div>
                <div className="sweep"></div>

                <div className="radar-core">
                  <div className="core">J</div>
                  <span>JARVIS</span>
                </div>

                {devices.map((device, index) => {
                  const threat = getThreat(device);
                  return (
                    <div
                      key={device.hostname}
                      className={`radar-node ${threat}`}
                      style={radarPosition(index, devices.length)}
                    >
                      <div></div>
                      <span>{device.hostname}</span>
                    </div>
                  );
                })}
              </div>

              <div className="radar-info">
                <span>{devices.length} DEVICES</span>
                <span>{events.length} EVENTS</span>
                <span>REAL-TIME</span>
              </div>
            </section>

            {/* RECENT SECURITY EVENTS */}
            <section className="glass events-section" aria-label="Recent Security Events">
              <div className="section-head">
                <span>RECENT SECURITY INTELLIGENCE</span>
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

          {/* RIGHT COLUMN: PROMINENT JARVIS CHAT CONSOLE (Rules 5, 6, 8, 9, 10, 29) */}
          <div className="right-column">
            <JarvisChat
              messages={chatMessages}
              onSendMessage={handleSendMessage}
              isProcessing={isProcessing}
              connectionStatus={connectionStatus}
            />
          </div>
        </main>
      )}
    </div>
  );
}