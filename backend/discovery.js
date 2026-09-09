const dgram = require("dgram");

const DISCOVERY_PORT = 5001;
const MAGIC_REQUEST = "CYBERFORESIGHT_DISCOVER_SERVER";
const MAGIC_RESPONSE = "CYBERFORESIGHT_SERVER_HERE";

function startDiscoveryBeacon(httpPort = 5000) {
    const socket = dgram.createSocket({ type: "udp4", reuseAddr: true });

    socket.on("error", (err) => {
        console.error("Discovery beacon error:", err.message);
    });

    socket.on("message", (msg, rinfo) => {
        const text = msg.toString().trim();
        if (text === MAGIC_REQUEST) {
            const response = JSON.stringify({
                tag: MAGIC_RESPONSE,
                port: httpPort,
                timestamp: Date.now()
            });

            socket.send(response, rinfo.port, rinfo.address, (err) => {
                if (err) {
                    console.error("Failed to respond to discovery probe:", err.message);
                } else {
                    console.log(`[Discovery] Responded to auto-discovery probe from ${rinfo.address}:${rinfo.port}`);
                }
            });
        }
    });

    socket.bind(DISCOVERY_PORT, "0.0.0.0", () => {
        try {
            socket.setBroadcast(true);
        } catch (e) {
            // ignore if not supported
        }
        console.log(`[Discovery] UDP beacon active on port ${DISCOVERY_PORT}`);
    });

    return socket;
}

module.exports = { startDiscoveryBeacon, DISCOVERY_PORT, MAGIC_REQUEST, MAGIC_RESPONSE };
