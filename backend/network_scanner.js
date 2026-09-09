const { execSync } = require("child_process");
const os = require("os");
const dgram = require("dgram");

const netBiosCache = {};

function resolveNetBiosName(ip) {
    if (process.platform !== "win32") return null;
    if (netBiosCache[ip] !== undefined) return netBiosCache[ip];
    netBiosCache[ip] = null;
    try {
        const out = execSync(`nbtstat -A ${ip}`, { timeout: 1500, windowsHide: true }).toString();
        const match = out.match(/<00>\s+UNIQUE\s+Registered\s+(\S+)/i);
        if (match) {
            netBiosCache[ip] = match[1].replace(/\.+$/, "");
        }
    } catch {
        // NetBIOS resolution ignored
    }
    return netBiosCache[ip];
}

function getLocalIpSet() {
    const ips = new Set(["127.0.0.1", "::1"]);
    const ifaces = os.networkInterfaces();
    for (const name in ifaces) {
        for (const iface of ifaces[name]) {
            if (iface.family === "IPv4") {
                ips.add(iface.address);
            }
        }
    }
    return ips;
}

function isMulticastOrBroadcast(ip, mac) {
    if (!ip || !mac) return true;
    if (ip.endsWith(".255") || ip.endsWith(".0")) return true;
    if (ip.startsWith("224.") || ip.startsWith("225.") || ip.startsWith("239.") || ip.startsWith("238.")) return true;
    if (ip === "255.255.255.255" || ip === "0.0.0.0") return true;

    const normalizedMac = mac.toLowerCase().replace(/[:-]/g, "-");
    if (normalizedMac === "ff-ff-ff-ff-ff-ff" || normalizedMac === "00-00-00-00-00-00") return true;
    if (normalizedMac.startsWith("01-00-5e")) return true; // IPv4 Multicast MAC

    return false;
}

function parseArpOutput(output, localIps) {
    const devices = [];
    const lines = output.split("\n");
    let currentInterface = "";

    for (let rawLine of lines) {
        const line = rawLine.trim();
        if (!line) continue;

        const ifaceMatch = line.match(/^Interface:\s*([0-9.]+)/i);
        if (ifaceMatch) {
            currentInterface = ifaceMatch[1];
            continue;
        }

        // Match IP MAC Type lines
        const entryMatch = line.match(/^([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})\s+([0-9a-fA-F[:-]{11,17})\s+(\w+)/);
        if (entryMatch) {
            const ip = entryMatch[1];
            const mac = entryMatch[2].replace(/:/g, "-").toUpperCase();
            const type = entryMatch[3].toLowerCase();

            if (localIps.has(ip)) continue;
            if (isMulticastOrBroadcast(ip, mac)) continue;

            // Ignore VMnet / VirtualBox standard gateway helper IPs (.254 on vm subnets)
            if (currentInterface.startsWith("192.168.37.") && ip === "192.168.37.254") continue;
            if (currentInterface.startsWith("192.168.147.") && ip === "192.168.147.254") continue;

            const isHotspot = currentInterface === "192.168.137.1" || ip.startsWith("192.168.137.");

            devices.push({
                ip,
                mac,
                type,
                interface: currentInterface,
                isHotspot
            });
        }
    }

    return devices;
}

function probeSubnet(subnetBase = "192.168.137") {
    // Sends light UDP packet to refresh ARP entries on the hotspot subnet
    const client = dgram.createSocket("udp4");
    const dummy = Buffer.from([0x00]);
    // Quick probe across dynamic pool
    for (let i = 2; i <= 254; i += 8) {
        try {
            client.send(dummy, 9, `${subnetBase}.${i}`, () => {});
        } catch {}
    }
    setTimeout(() => {
        try { client.close(); } catch {}
    }, 500);
}

function scanNetworkDevices() {
    const localIps = getLocalIpSet();
    let arpOutput = "";

    try {
        arpOutput = execSync("arp -a", { timeout: 3000, windowsHide: true }).toString();
    } catch (err) {
        console.error("[Scanner] arp -a error:", err.message);
        return [];
    }

    const rawDevices = parseArpOutput(arpOutput, localIps);
    const discovered = [];

    for (const dev of rawDevices) {
        const netName = resolveNetBiosName(dev.ip);
        let name = netName;
        if (!name) {
            if (dev.isHotspot) {
                name = `Hotspot Device (${dev.ip})`;
            } else {
                name = `LAN Device (${dev.ip})`;
            }
        }

        discovered.push({
            hostname: `dev-${dev.ip.replace(/\./g, "-")}`,
            name: name,
            ip: dev.ip,
            mac: dev.mac,
            os: dev.isHotspot ? "Hotspot Client" : "Network Device",
            cpu: 0,
            ram: 0,
            status: "ONLINE",
            source: "auto-discovered",
            isHotspot: dev.isHotspot
        });
    }

    return discovered;
}

function startAutoDiscovery({ onDeviceFound, intervalMs = 5000 }) {
    console.log(`[Auto-Discovery] Network & Hotspot Device Scanner active (Interval: ${intervalMs}ms)`);

    const runScan = () => {
        probeSubnet("192.168.137"); // Keep hotspot ARP cache alive

        try {
            const devices = scanNetworkDevices();
            for (const dev of devices) {
                if (typeof onDeviceFound === "function") {
                    onDeviceFound(dev);
                }
            }
        } catch (e) {
            console.error("[Auto-Discovery] Scan error:", e.message);
        }
    };

    // Run first scan immediately
    setTimeout(runScan, 1000);
    const timer = setInterval(runScan, intervalMs);

    return {
        stop: () => clearInterval(timer),
        scanNow: runScan
    };
}

module.exports = {
    scanNetworkDevices,
    startAutoDiscovery,
    resolveNetBiosName
};
