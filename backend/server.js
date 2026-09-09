const express = require("express");
const http = require("http");
const cors = require("cors");
const { Server } = require("socket.io");
const { spawn, execFileSync } = require("child_process");
const osModule = require("os");
const path = require("path");
const fs = require("fs");

const app = express();
const server = http.createServer(app);

app.use(cors());
app.use(express.json());

const io = new Server(server, {
    cors: {
        origin: "*"
    }
});

const worldModel = {
    timestamp: new Date().toISOString(),
    devices: {},
    recentEvents: []
};

function updateWorldTimestamp() {
    worldModel.timestamp = new Date().toISOString();
}

function runJARVIS(worldState) {

    return new Promise((resolve, reject) => {

        const pythonPath = path.join(
            __dirname,
            "..",
            ".venv",
            "Scripts",
            "python.exe"
        );

        const bridgePath = path.join(
            __dirname,
            "jarvis_bridge.py"
        );

        const python = spawn(
            pythonPath,
            [bridgePath],
            {
                cwd: path.join(__dirname, "..")
            }
        );

        let output = "";
        let errorOutput = "";

        python.stdout.on("data", (data) => {
            output += data.toString();
        });

        python.stderr.on("data", (data) => {
            errorOutput += data.toString();
        });

        python.on("error", (error) => {
            reject(error);
        });

        python.on("close", (code) => {

            if (code !== 0) {
                return reject(
                    new Error(
                        errorOutput ||
                        `Python exited with code ${code}`
                    )
                );
            }

            try {

                const lines = output
                    .trim()
                    .split("\n");

                const jsonLine =
                    lines[lines.length - 1];

                const result =
                    JSON.parse(jsonLine);

                resolve(result);

            } catch (error) {

                reject(
                    new Error(
                        "Invalid JARVIS response: " +
                        error.message
                    )
                );
            }
        });

        python.stdin.write(
            JSON.stringify(worldState)
        );

        python.stdin.end();
    });
}


// ==========================================
// DEVICE HISTORY PERSISTENCE (LOCAL-FIRST)
// ==========================================

const DATA_DIR = path.join(__dirname, "..", "data");
const DEVICE_HISTORY_FILE = path.join(DATA_DIR, "device_history.json");

function formatDuration(sec) {
    if (sec < 60) return `${sec}s`;
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    if (m < 60) return `${m}m ${s}s`;
    const h = Math.floor(m / 60);
    const remM = m % 60;
    return `${h}h ${remM}m ${s}s`;
}

let deviceHistory = [];

function loadDeviceHistory() {
    try {
        if (!fs.existsSync(DATA_DIR)) {
            fs.mkdirSync(DATA_DIR, { recursive: true });
        }
        if (fs.existsSync(DEVICE_HISTORY_FILE)) {
            const data = JSON.parse(fs.readFileSync(DEVICE_HISTORY_FILE, "utf8"));
            if (Array.isArray(data)) {
                const restartIso = new Date().toISOString();
                deviceHistory = data.map((s) => {
                    if (s.status === "ONLINE") {
                        const disconnectedAt = s.lastSeen || restartIso;
                        const durSec = Math.max(
                            0,
                            Math.floor((new Date(disconnectedAt) - new Date(s.connectedAt)) / 1000)
                        );
                        return {
                            ...s,
                            status: "OFFLINE",
                            disconnectedAt,
                            duration: formatDuration(durSec)
                        };
                    }
                    return s;
                });
                saveDeviceHistory();
                return;
            }
        }
    } catch (err) {
        console.error("Error loading device_history.json:", err.message);
    }
    deviceHistory = [];
}

function saveDeviceHistory() {
    try {
        if (!fs.existsSync(DATA_DIR)) {
            fs.mkdirSync(DATA_DIR, { recursive: true });
        }
        fs.writeFileSync(DEVICE_HISTORY_FILE, JSON.stringify(deviceHistory, null, 2), "utf8");
    } catch (err) {
        console.error("Error saving device_history.json:", err.message);
    }
}

function getDeviceHistorySummary() {
    const totalDevices = new Set(deviceHistory.map((s) => s.hostname)).size;
    const activeDevices = Object.keys(worldModel.devices).length;
    return {
        totalDevices,
        activeDevices,
        totalSessions: deviceHistory.length,
        sessions: deviceHistory
    };
}

loadDeviceHistory();


// ==========================================
// LIVE ATTACK LAB (demo/live_sim.py bridge)
// ==========================================

const liveSim = {
    child: null,
    startedAt: null,
    last: null,
    buffered: ""
};

function startLiveSim(tick, k, threshold) {
    return new Promise((resolve, reject) => {
        if (liveSim.child) {
            return resolve({ running: true });
        }

        const pythonPath = path.join(
            __dirname,
            "..",
            ".venv",
            "Scripts",
            "python.exe"
        );

        const simPath = path.join(
            __dirname,
            "..",
            "demo",
            "live_sim.py"
        );

        const args = [simPath, "--tick", String(tick ?? 1.0)];
        if (k) args.push("--k", String(k));
        if (threshold) args.push("--threshold", String(threshold));

        const child = spawn(
            pythonPath,
            args,
            {
                cwd: path.join(__dirname, "..")
            }
        );

        liveSim.child = child;
        liveSim.startedAt = new Date().toISOString();

        child.stdout.on("data", (data) => {
            liveSim.buffered += data.toString();
            let idx;
            while ((idx = liveSim.buffered.indexOf("\n")) !== -1) {
                const line = liveSim.buffered
                    .slice(0, idx)
                    .trim();
                liveSim.buffered =
                    liveSim.buffered.slice(idx + 1);
                if (!line) continue;

                let msg;
                try {
                    msg = JSON.parse(line);
                } catch {
                    continue;
                }

                if (msg.type === "state") {
                    liveSim.last = msg;
                    io.emit("live_sim_state", msg);
                } else {
                    io.emit("live_sim_ctrl", msg);
                }
            }
        });

        child.stderr.on("data", (data) => {
            process.stderr.write(data.toString());
        });

        child.on("error", (error) => {
            liveSim.child = null;
            io.emit("live_sim_error", {
                error: error.message
            });
            reject(error);
        });

        child.on("close", (code) => {
            const wasRunning =
                liveSim.child === child;
            liveSim.child = null;
            liveSim.buffered = "";
            if (wasRunning) {
                io.emit("live_sim_ctrl", {
                    type: "stopped",
                    code
                });
            }
        });

        child.on("spawn", () => {
            resolve({ running: true });
        });
    });
}

function stopLiveSim() {
    if (liveSim.child) {
        liveSim.child.kill();
        return true;
    }
    return false;
}

app.get("/live-sim/state", (req, res) => {
    res.json({
        running: Boolean(liveSim.child),
        startedAt: liveSim.startedAt,
        last: liveSim.last
    });
});

app.post("/live-sim/start", async (req, res) => {
    try {
        const body = req.body || {};
        const result = await startLiveSim(
            body.tick,
            body.k,
            body.threshold
        );
        res.json({ success: true, ...result });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.post("/live-sim/stop", (req, res) => {
    const stopped = stopLiveSim();
    res.json({ success: true, stopped });
});

app.post("/live-sim/command", (req, res) => {
    const { cmd } = req.body || {};
    if (!cmd) {
        return res.status(400).json({
            success: false,
            error: "cmd is required"
        });
    }
    if (!liveSim.child) {
        return res.status(409).json({
            success: false,
            error: "live sim not running"
        });
    }
    liveSim.child.stdin.write(
        JSON.stringify({ cmd }) + "\n"
    );
    res.json({
        success: true,
        cmd
    });
});


// ==========================================
// CYBERFORESIGHT FORECAST ARTIFACTS
// ==========================================

const MODELS_DIR = path.join(__dirname, "..", "models");

function readJsonIfExists(name) {
    const file = path.join(MODELS_DIR, name);
    if (!fs.existsSync(file)) return null;
    try {
        return JSON.parse(fs.readFileSync(file, "utf8"));
    } catch {
        return null;
    }
}

function csvToRows(name) {
    const file = path.join(MODELS_DIR, name);
    if (!fs.existsSync(file)) return null;
    const clean = (s) => (s === undefined ? "" : String(s).replace(/\r$/, ""));
    const lines = fs.readFileSync(file, "utf8").trim().split("\n");
    if (lines.length < 2) return null;
    const headers = lines[0].split(",").map(clean);
    return lines.slice(1).map((line) => {
        const values = line.split(",").map(clean);
        const row = {};
        headers.forEach((h, i) => { row[h] = values[i]; });
        return row;
    });
}

function detectModelType(forecast) {
    if (forecast.info && forecast.info.model_type) {
        const m = String(forecast.info.model_type).trim();
        if (m.toLowerCase().includes("transformer")) return "Temporal Transformer";
        if (m.toLowerCase().includes("lstm")) return "LSTM fallback";
        return m;
    }
    if (forecast.benchmarkMetrics) {
        const keys = Object.keys(forecast.benchmarkMetrics);
        if (keys.some((k) => k.toLowerCase().includes("transformer"))) {
            return "Temporal Transformer";
        }
        if (keys.some((k) => k.toLowerCase().includes("lstm"))) {
            return "LSTM fallback";
        }
    }
    const trainMetrics = readJsonIfExists("train_metrics.json");
    if (trainMetrics && trainMetrics.model_type) {
        const m = String(trainMetrics.model_type).trim();
        if (m.toLowerCase().includes("transformer")) return "Temporal Transformer";
        if (m.toLowerCase().includes("lstm")) return "LSTM fallback";
        return m;
    }
    return "Temporal Transformer";
}

app.get(
    "/forecast",
    (req, res) => {

        const forecast = {
            info: readJsonIfExists("forecast_info.json"),
            timeline: csvToRows("forecast_timeline.csv"),
            rollout: csvToRows("forecast_rollout.csv"),
            attention: readJsonIfExists("explain_attention.json"),
            shap: readJsonIfExists("explain_shap.json"),
            benchmarkMetrics: readJsonIfExists("benchmark_metrics.json"),
            benchmarkCompare: csvToRows("benchmark_compare.csv")
        };

        const ready = Boolean(
            forecast.info &&
            forecast.timeline &&
            forecast.rollout
        );

        const modelType = detectModelType(forecast);

        res.json({
            success: true,
            ready,
            modelType,
            demoCommand:
                ".venv\\Scripts\\python run.py --stage features && " +
                "run.py --stage train && run.py --stage forecast && " +
                "run.py --stage explain && run.py --stage benchmark",
            forecast
        });
    }
);


// ==========================================
// HOME
// ==========================================

const distDir = path.join(
    __dirname,
    "..",
    "frontend",
    "dist"
);

if (fs.existsSync(
    path.join(distDir, "index.html")
)) {
    app.use(express.static(distDir));

    app.get("/", (req, res) => {
        res.sendFile(
            path.join(distDir, "index.html")
        );
    });
} else {
    app.get("/", (req, res) => {
        res.json({
            status: "JARVIS backend online"
        });
    });
}


// ==========================================
// DEVICE
// ==========================================

const netBiosCache = {};

function resolveNetBiosName(ip) {
    if (process.platform !== "win32") return null;
    if (netBiosCache[ip] !== undefined) return netBiosCache[ip];
    netBiosCache[ip] = null;
    try {
        const out = execFileSync(
            "nbtstat",
            ["-A", ip],
            { timeout: 2500, windowsHide: true }
        ).toString();
        const match = out.match(
            /<00>\s+UNIQUE\s+Registered\s+(\S+)/i
        );
        if (match) {
            netBiosCache[ip] = match[1].replace(/\.+$/, "");
        }
    } catch (e) {
        // no NETBIOS answer
    }
    return netBiosCache[ip];
}

function uniqueDeviceName(base, devices, currentHostname) {
    if (!(base || "").trim()) return "";
    const used = {};
    for (const id in devices) {
        if (id === currentHostname) continue;
        used[devices[id].name || ""] = true;
    }
    if (!used[base]) return base;
    let n = 2;
    while (used[base + ` (${n})`]) n++;
    return base + ` (${n})`;
}

app.post("/device", (req, res) => {

    const device = req.body;

    if (!device.hostname) {
        return res.status(400).json({
            success: false,
            error: "hostname is required"
        });
    }

    const ip = (
        device.ip ||
        (req.ip || "").replace(/^::ffff:/, "") ||
        "UNKNOWN"
    );

    const netName = resolveNetBiosName(ip);
    let realName = (device.name || "").trim() || netName || null;

    if (!realName && (ip === "127.0.0.1" || ip === "::1")) {
        realName = osModule.hostname();
    }

    const nowIso = new Date().toISOString();

    const updatedDevice = {
        hostname: device.hostname,
        name: uniqueDeviceName(
            realName || "",
            worldModel.devices,
            device.hostname
        ),
        ip: ip,
        os: device.os || "UNKNOWN",
        cpu: device.cpu || 0,
        ram: device.ram || 0,
        status: device.status || "ONLINE",
        lastSeen: nowIso
    };

    worldModel.devices[device.hostname] = updatedDevice;
    updateWorldTimestamp();

    // Session tracking
    let activeSession = deviceHistory.find(
        (s) => s.hostname === device.hostname && s.status === "ONLINE"
    );

    if (!activeSession) {
        const sessId = "sess_" + Date.now() + "_" + Math.random().toString(36).substring(2, 7);
        activeSession = {
            id: sessId,
            deviceId: device.hostname,
            hostname: device.hostname,
            name: updatedDevice.name || device.hostname,
            ip: ip,
            os: device.os || "UNKNOWN",
            firstSeen: nowIso,
            lastSeen: nowIso,
            connectedAt: nowIso,
            disconnectedAt: null,
            status: "ONLINE",
            duration: "0s"
        };
        deviceHistory.unshift(activeSession);
        saveDeviceHistory();

        io.emit("device_history_update", {
            action: "connected",
            session: activeSession,
            history: getDeviceHistorySummary()
        });
    } else {
        activeSession.lastSeen = nowIso;
        if (ip && ip !== "UNKNOWN") activeSession.ip = ip;
        if (device.os && device.os !== "UNKNOWN") activeSession.os = device.os;
        if (updatedDevice.name) activeSession.name = updatedDevice.name;
        const durSec = Math.max(
            0,
            Math.floor((new Date(nowIso) - new Date(activeSession.connectedAt)) / 1000)
        );
        activeSession.duration = formatDuration(durSec);
    }

    console.log("DEVICE:", (updatedDevice.name || updatedDevice.hostname), "@", ip);

    io.emit("device_update", updatedDevice);
    io.emit("world_update", worldModel);

    res.json({
        success: true,
        device: updatedDevice
    });
});


// ==========================================
// SECURITY EVENT
// ==========================================

app.post(
    "/security-event",
    (req, res) => {

        const event = {
            ...req.body,
            timestamp: new Date().toISOString()
        };

        worldModel.recentEvents.push(event);

        if (worldModel.recentEvents.length > 100) {
            worldModel.recentEvents = worldModel.recentEvents.slice(-100);
        }

        updateWorldTimestamp();

        console.log("SECURITY EVENT:", event);

        io.emit("security_event", event);
        io.emit("world_update", worldModel);

        res.json({
            success: true,
            event: event,
            message: "Security event received. JARVIS analysis started."
        });

        const snapshot = JSON.parse(JSON.stringify(worldModel));
        runJARVIS(snapshot)
            .then((result) => {
                io.emit("jarvis_intelligence", result);
            })
            .catch((error) => {
                console.error("JARVIS ERROR:", error.message);
                io.emit("jarvis_error", { error: error.message });
            });
    }
);


// ==========================================
// VOICE / TEXT COMMAND
// ==========================================

app.post(
    "/voice-command",
    async (req, res) => {

        const { command } = req.body;

        if (!command) {
            return res.status(400).json({
                success: false,
                message: "Voice command is required"
            });
        }

        console.log("VOICE COMMAND:", command);

        try {
            const snapshot = JSON.parse(JSON.stringify(worldModel));
            snapshot.voice_command = command;

            const result = await runJARVIS(snapshot);

            res.json({
                success: true,
                command: command,
                result: result
            });
        } catch (error) {
            console.error("Voice command error:", error.message);
            res.status(500).json({
                success: false,
                message: "JARVIS voice processing failed",
                error: error.message
            });
        }
    }
);


// ==========================================
// DEVICES & WORLD STATE
// ==========================================

app.get("/devices", (req, res) => {
    res.json(Object.values(worldModel.devices));
});

app.get("/world-state", (req, res) => {
    res.json(worldModel);
});

app.get("/device-history", (req, res) => {
    res.json({
        success: true,
        ...getDeviceHistorySummary()
    });
});


// ==========================================
// SOCKET.IO
// ==========================================

io.on("connection", (socket) => {
    console.log("Client connected:", socket.id);
    socket.emit("world_update", worldModel);
    socket.emit("device_history_update", {
        action: "init",
        history: getDeviceHistorySummary()
    });

    socket.on("disconnect", () => {
        console.log("Client disconnected:", socket.id);
    });
});

setInterval(() => {
    const now = Date.now();
    let changed = false;

    for (const hostname in worldModel.devices) {
        const lastSeen = new Date(
            worldModel.devices[hostname].lastSeen
        ).getTime();

        if (now - lastSeen > 15000) {
            console.log(`Device offline: ${hostname}`);
            const disconnectIso = new Date().toISOString();

            const activeSession = deviceHistory.find(
                (s) => s.hostname === hostname && s.status === "ONLINE"
            );
            if (activeSession) {
                activeSession.status = "OFFLINE";
                activeSession.disconnectedAt = disconnectIso;
                activeSession.lastSeen = worldModel.devices[hostname].lastSeen || disconnectIso;
                const durSec = Math.max(
                    0,
                    Math.floor((new Date(disconnectIso) - new Date(activeSession.connectedAt)) / 1000)
                );
                activeSession.duration = formatDuration(durSec);
            }

            delete worldModel.devices[hostname];
            changed = true;
        }
    }

    if (changed) {
        saveDeviceHistory();
        io.emit("world_update", worldModel);
        io.emit("device_history_update", {
            action: "disconnected",
            history: getDeviceHistorySummary()
        });
    }
}, 5000);


const { startDiscoveryBeacon } = require("./discovery");

// ==========================================
// START SERVER
// ==========================================

server.listen(
    5000,
    "0.0.0.0",
    () => {
        console.log("JARVIS backend running on port 5000");

        try {
            startDiscoveryBeacon(5000);
        } catch (e) {
            console.error("Could not start discovery beacon:", e.message);
        }
    }
);
