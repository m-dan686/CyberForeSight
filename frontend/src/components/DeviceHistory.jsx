import { useEffect, useState } from "react";

const API_HISTORY = "http://localhost:5000/device-history";

const fmtDate = (iso) => {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return "—";
  }
};

export default function DeviceHistory({ socket }) {
  const [data, setData] = useState({
    totalDevices: 0,
    activeDevices: 0,
    totalSessions: 0,
    sessions: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const fetchHistory = () => {
    setLoading(true);
    fetch(API_HISTORY)
      .then((res) => {
        if (!res.ok) throw new Error("Backend response error");
        return res.json();
      })
      .then((json) => {
        setData({
          totalDevices: json.totalDevices || 0,
          activeDevices: json.activeDevices || 0,
          totalSessions: json.totalSessions || (json.sessions || []).length,
          sessions: json.sessions || [],
        });
        setError(null);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to load device history");
        setLoading(false);
      });
  };

  useEffect(() => {
    let cancelled = false;

    fetch(API_HISTORY)
      .then((res) => {
        if (!res.ok) throw new Error("Backend response error");
        return res.json();
      })
      .then((json) => {
        if (!cancelled) {
          setData({
            totalDevices: json.totalDevices || 0,
            activeDevices: json.activeDevices || 0,
            totalSessions: json.totalSessions || (json.sessions || []).length,
            sessions: json.sessions || [],
          });
          setError(null);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load device history");
          setLoading(false);
        }
      });

    if (!socket) {
      return () => {
        cancelled = true;
      };
    }

    const handleUpdate = (payload) => {
      if (payload && payload.history) {
        setData({
          totalDevices: payload.history.totalDevices || 0,
          activeDevices: payload.history.activeDevices || 0,
          totalSessions: payload.history.totalSessions || (payload.history.sessions || []).length,
          sessions: payload.history.sessions || [],
        });
      }
    };

    socket.on("device_history_update", handleUpdate);
    return () => {
      cancelled = true;
      socket.off("device_history_update", handleUpdate);
    };
  }, [socket]);

  const filteredSessions = data.sessions.filter((s) => {
    const q = search.trim().toLowerCase();
    const matchesSearch =
      !q ||
      (s.hostname && s.hostname.toLowerCase().includes(q)) ||
      (s.ip && s.ip.toLowerCase().includes(q)) ||
      (s.os && s.os.toLowerCase().includes(q));

    const matchesStatus =
      statusFilter === "ALL" ||
      (statusFilter === "ONLINE" && s.status === "ONLINE") ||
      (statusFilter === "OFFLINE" && s.status === "OFFLINE");

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="history-view">
      <div className="history-head">
        <div>
          <h2>DEVICE SESSION HISTORY</h2>
          <p>Real-time & persisted security telemetry · server session audit</p>
        </div>

        <div className="history-actions">
          <button
            type="button"
            className="history-refresh-btn"
            onClick={fetchHistory}
            disabled={loading}
            aria-label="Refresh device history"
          >
            {loading ? "Refreshing..." : "↻ Refresh Audit"}
          </button>
        </div>
      </div>

      {/* KPI STATS */}
      <div className="history-kpis">
        <div className="history-kpi">
          <span className="history-kpi-label">TOTAL MONITORED DEVICES</span>
          <strong className="history-kpi-val">{data.totalDevices}</strong>
        </div>
        <div className="history-kpi k-active">
          <span className="history-kpi-label">CURRENTLY ACTIVE</span>
          <strong className="history-kpi-val">{data.activeDevices}</strong>
        </div>
        <div className="history-kpi">
          <span className="history-kpi-label">HISTORICAL SESSIONS</span>
          <strong className="history-kpi-val">{data.totalSessions}</strong>
        </div>
      </div>

      {/* CONTROLS */}
      <div className="history-controls">
        <div className="history-search-box">
          <input
            type="text"
            placeholder="Search by hostname, IP or OS..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search devices"
          />
        </div>

        <div className="history-filter-group" role="group" aria-label="Status filter">
          <button
            type="button"
            className={statusFilter === "ALL" ? "active" : ""}
            onClick={() => setStatusFilter("ALL")}
            aria-pressed={statusFilter === "ALL"}
          >
            All Sessions
          </button>
          <button
            type="button"
            className={statusFilter === "ONLINE" ? "active" : ""}
            onClick={() => setStatusFilter("ONLINE")}
            aria-pressed={statusFilter === "ONLINE"}
          >
            Online Only
          </button>
          <button
            type="button"
            className={statusFilter === "OFFLINE" ? "active" : ""}
            onClick={() => setStatusFilter("OFFLINE")}
            aria-pressed={statusFilter === "OFFLINE"}
          >
            Offline Only
          </button>
        </div>
      </div>

      {/* TABLE */}
      <div className="history-table-container">
        {error && (
          <div className="history-error-card">
            <h3>Backend Offline</h3>
            <p>Unable to connect to <code>{API_HISTORY}</code>. Start backend with <code>node backend/server.js</code>.</p>
          </div>
        )}

        {!error && loading && data.sessions.length === 0 && (
          <div className="history-empty">Loading device session history…</div>
        )}

        {!error && !loading && data.sessions.length === 0 && (
          <div className="history-empty">NO DEVICE HISTORY AVAILABLE</div>
        )}

        {!error && data.sessions.length > 0 && filteredSessions.length === 0 && (
          <div className="history-empty">No sessions match the filter criteria.</div>
        )}

        {!error && filteredSessions.length > 0 && (
          <table className="history-table">
            <thead>
              <tr>
                <th>DEVICE</th>
                <th>IP ADDRESS</th>
                <th>OS</th>
                <th>STATUS</th>
                <th>CONNECTED</th>
                <th>LAST SEEN</th>
                <th>DISCONNECTED</th>
                <th>SESSION DURATION</th>
              </tr>
            </thead>
            <tbody>
              {filteredSessions.map((s) => (
                <tr key={s.id}>
                  <td>
                    <strong className="history-host">{s.hostname}</strong>
                  </td>
                  <td>
                    <span className="history-ip">{s.ip || "UNKNOWN"}</span>
                  </td>
                  <td>
                    <span className="history-os">{s.os || "UNKNOWN"}</span>
                  </td>
                  <td>
                    <span className={`history-badge ${s.status === "ONLINE" ? "badge-online" : "badge-offline"}`}>
                      ● {s.status}
                    </span>
                  </td>
                  <td>{fmtDate(s.connectedAt || s.firstSeen)}</td>
                  <td>{fmtDate(s.lastSeen)}</td>
                  <td>{s.disconnectedAt ? fmtDate(s.disconnectedAt) : "—"}</td>
                  <td>
                    <span className="history-dur">{s.duration || "0s"}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
