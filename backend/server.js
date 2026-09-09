const express = require("express");
const http = require("http");
const cors = require("cors");
const { Server } = require("socket.io");
const { spawn } = require("child_process");
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
                // On backend restart, ensure previous sessions marked "ONLINE" are closed (Rule 48)
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
    // 1. Existing forecast artifact metadata (forecast_info.json)
    if (forecast.info && forecast.info.model_type) {
        const m = String(forecast.info.model_type).trim();
        if (m.toLowerCase().includes("transformer")) return "Temporal Transformer";
        if (m.toLowerCase().includes("lstm")) return "LSTM fallback";
        return m;
    }

    // 2. Benchmark metrics artifact (benchmark_metrics.json)
    if (forecast.benchmarkMetrics) {
        const keys = Object.keys(forecast.benchmarkMetrics);
        if (keys.some((k) => k.toLowerCase().includes("transformer"))) {
            return "Temporal Transformer";
        }
        if (keys.some((k) => k.toLowerCase().includes("lstm"))) {
            return "LSTM fallback";
        }
    }

    // 3. Training metrics artifact
    const trainMetrics = readJsonIfExists("train_metrics.json");
    if (trainMetrics && trainMetrics.model_type) {
        const m = String(trainMetrics.model_type).trim();
        if (m.toLowerCase().includes("transformer")) return "Temporal Transformer";
        if (m.toLowerCase().includes("lstm")) return "LSTM fallback";
        return m;
    }

    // 4. Validated fallback: configs/world_model.yaml (parsed via regex, zero new dependencies)
    try {
        const configPath = path.join(__dirname, "..", "configs", "world_model.yaml");
        if (fs.existsSync(configPath)) {
            const raw = fs.readFileSync(configPath, "utf8");
            const match = raw.match(/^\s*type:\s*["']?([^"'\r\n]+)["']?/m);
            if (match && match[1]) {
                const val = match[1].trim().toLowerCase();
                if (val.includes("transformer")) return "Temporal Transformer";
                if (val.includes("lstm")) return "LSTM fallback";
                return match[1].trim();
            }
        }
    } catch {
        // ignore
    }

    return "MODEL METADATA UNAVAILABLE";
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

app.get("/", (req, res) => {

    res.json({
        status: "JARVIS backend online"
    });
});


// ==========================================
// DEVICE
// ==========================================

app.post("/device", (req, res) => {

    const device = req.body;

    if (!device.hostname) {

        return res.status(400).json({
            success: false,
            error: "hostname is required"
        });
    }

    const nowIso = new Date().toISOString();

    const updatedDevice = {

        hostname: device.hostname,

        ip: device.ip || "UNKNOWN",

        os: device.os || "UNKNOWN",

        cpu: device.cpu || 0,

        ram: device.ram || 0,

        status: device.status || "ONLINE",

        lastSeen: nowIso
    };

    worldModel.devices[
        device.hostname
    ] = updatedDevice;

    updateWorldTimestamp();

    // Session tracking (Rules 15, 16, 17: Heartbeat != new session)
    let activeSession = deviceHistory.find(
        (s) => s.hostname === device.hostname && s.status === "ONLINE"
    );

    if (!activeSession) {
        // Device connects or reconnects: create a new session
        const sessId = "sess_" + Date.now() + "_" + Math.random().toString(36).substring(2, 7);
        activeSession = {
            id: sessId,
            deviceId: device.hostname,
            hostname: device.hostname,
            ip: device.ip || "UNKNOWN",
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
        // Existing active session heartbeat: update lastSeen and duration without duplicate row
        activeSession.lastSeen = nowIso;
        if (device.ip && device.ip !== "UNKNOWN") activeSession.ip = device.ip;
        if (device.os && device.os !== "UNKNOWN") activeSession.os = device.os;
        const durSec = Math.max(
            0,
            Math.floor((new Date(nowIso) - new Date(activeSession.connectedAt)) / 1000)
        );
        activeSession.duration = formatDuration(durSec);
    }

    console.log(
        "DEVICE:",
        device.hostname
    );

    io.emit(
        "device_update",
        updatedDevice
    );

    io.emit(
        "world_update",
        worldModel
    );

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

            timestamp:
                new Date().toISOString()
        };

        worldModel.recentEvents.push(
            event
        );

        if (
            worldModel.recentEvents.length > 100
        ) {

            worldModel.recentEvents =
                worldModel.recentEvents.slice(-100);
        }

        updateWorldTimestamp();

        console.log(
            "SECURITY EVENT:",
            event
        );

        io.emit(
            "security_event",
            event
        );

        io.emit(
            "world_update",
            worldModel
        );


        // Respond immediately
        res.json({

            success: true,

            event: event,

            message:
                "Security event received. JARVIS analysis started."

        });


        // Run JARVIS in background

        const snapshot =
            JSON.parse(
                JSON.stringify(
                    worldModel
                )
            );

        console.log(
            "JARVIS: Analyzing security event..."
        );

        runJARVIS(snapshot)

            .then((result) => {

                console.log(
                    "JARVIS: Analysis complete"
                );

                io.emit(
                    "jarvis_intelligence",
                    result
                );

            })

            .catch((error) => {

                console.error(
                    "JARVIS ERROR:",
                    error.message
                );

                io.emit(
                    "jarvis_error",
                    {
                        error:
                            error.message
                    }
                );
            });
    }
);


// ==========================================
// VOICE COMMAND
// ==========================================

app.post(
    "/voice-command",
    async (req, res) => {

        const { command } = req.body;

        if (!command) {

            return res.status(400).json({
                success: false,
                message:
                    "Voice command is required"
            });
        }

        console.log(
            "VOICE COMMAND:",
            command
        );

        try {

            const snapshot =
                JSON.parse(
                    JSON.stringify(
                        worldModel
                    )
                );

            snapshot.voice_command =
                command;

            const result =
                await runJARVIS(
                    snapshot
                );

            console.log(
                "JARVIS: Voice response complete"
            );

            res.json({

                success: true,

                command: command,

                result: result

            });

        } catch (error) {

            console.error(
                "Voice command error:",
                error.message
            );

            res.status(500).json({

                success: false,

                message:
                    "JARVIS voice processing failed",

                error:
                    error.message

            });
        }
    }
);


// ==========================================
// DEVICES
// ==========================================

app.get(
    "/devices",
    (req, res) => {

        res.json(
            Object.values(
                worldModel.devices
            )
        );
    }
);


// ==========================================
// WORLD STATE
// ==========================================

app.get(
    "/world-state",
    (req, res) => {

        res.json(
            worldModel
        );
    }
);


// ==========================================
// DEVICE HISTORY
// ==========================================

app.get(
    "/device-history",
    (req, res) => {

        res.json({
            success: true,
            ...getDeviceHistorySummary()
        });
    }
);


// ==========================================
// SOCKET.IO
// ==========================================

io.on(
    "connection",
    (socket) => {

        console.log(
            "Client connected:",
            socket.id
        );

        socket.emit(
            "world_update",
            worldModel
        );

        socket.emit(
            "device_history_update",
            {
                action: "init",
                history: getDeviceHistorySummary()
            }
        );

        socket.on(
            "disconnect",
            () => {

                console.log(
                    "Client disconnected:",
                    socket.id
                );
            }
        );
    }
);

// Remove devices that have not sent a heartbeat for 15 seconds (Rules 15, 49)
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

            // Find and close active session
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


// ==========================================
// START SERVER
// ==========================================

server.listen(
    5000,
    "0.0.0.0",
    () => {

        console.log(
            "JARVIS backend running on port 5000"
        );
    }
);