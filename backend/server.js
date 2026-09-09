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

        res.json({
            success: true,
            ready,
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

    const indexPath = path.join(
        __dirname,
        "..",
        "frontend",
        "dist",
        "index.html"
    );

    if (fs.existsSync(indexPath)) {
        return res.sendFile(indexPath);
    }

    res.json({
        status: "JARVIS backend online"
    });
});


// ==========================================
// DEVICE
// ==========================================

// Best-effort NETBIOS name resolution for Windows clients (cached per IP).
// Phones and Macs don't answer NETBIOS -> resolveNetBiosName returns null.
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
        // no NETBIOS answer — keep cache[ip] = null
    }
    return netBiosCache[ip];
}

// Keep display names unique among currently connected devices.
// Empty nameless devices are not deduplicated (they show as their IP).
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

    // Real device name only: user-set > NETBIOS > host computer name
    // (for the backend machine itself, e.g. loopback). Never invented
    // labels or generic device types.
    const netName = resolveNetBiosName(ip);

    let realName = (device.name || "").trim() || netName || null;

    if (!realName && (ip === "127.0.0.1" || ip === "::1")) {
        realName = osModule.hostname();
    }

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

        status: device.status || "UNKNOWN",

        lastSeen:
            new Date().toISOString()
    };

    worldModel.devices[
        device.hostname
    ] = updatedDevice;

    updateWorldTimestamp();

    console.log(
        "DEVICE:",
        (updatedDevice.name || updatedDevice.ip),
        "@",
        updatedDevice.ip
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
// Remove devices that have not sent a heartbeat for 15 seconds
setInterval(() => {
    const now = Date.now();
    let changed = false;

    for (const hostname in worldModel.devices) {
        const lastSeen = new Date(
            worldModel.devices[hostname].lastSeen
        ).getTime();

        if (now - lastSeen > 15000) {
            console.log(`Device offline: ${hostname}`);

            delete worldModel.devices[hostname];
            changed = true;
        }
    }

    if (changed) {
        io.emit("world_update", worldModel);
    }
}, 5000);


// ==========================================
// FRONTEND (built dist served on same port)
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

    app.get("/*splat", (req, res) => {
        res.sendFile(
            path.join(distDir, "index.html")
        );
    });
}


const { startDiscoveryBeacon } = require("./discovery");

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

        // Start UDP auto-discovery beacon on LAN
        try {
            startDiscoveryBeacon(5000);
        } catch (e) {
            console.error("Could not start discovery beacon:", e.message);
        }
    }
);