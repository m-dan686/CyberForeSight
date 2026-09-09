"""
CyberForeSight - Silent Client Hardware & Telemetry Agent
Runs completely in the background on client laptops.
- Auto-discovers the CyberForeSight server on the LAN via UDP probe.
- Collects real-time hardware status (Hostname, OS, CPU cores, live CPU %, RAM GB & usage %).
- Sends periodic heartbeats to /device. No browser or user action needed.
"""

import sys
import time
import socket
import json
import platform
import os
import urllib.request
import urllib.error

# Try importing psutil for high-accuracy metrics; fallback gracefully to stdlib
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

DISCOVERY_PORT = 5001
MAGIC_REQUEST = b"CYBERFORESIGHT_DISCOVER_SERVER"
MAGIC_RESPONSE = "CYBERFORESIGHT_SERVER_HERE"


def get_hardware_info():
    """Reads system hardware metrics without browser dependency."""
    hostname = socket.gethostname()
    os_name = f"{platform.system()} {platform.release()}"

    if HAS_PSUTIL:
        cpu_cores = psutil.cpu_count(logical=True) or 1
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        ram_gb = round(mem.total / (1024 ** 3), 1)
        ram_percent = mem.percent
    else:
        cpu_cores = os.cpu_count() or 1
        cpu_percent = 0
        ram_gb = 0
        ram_percent = 0
        # Windows ctypes fallback (no pip install required)
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                ram_gb = round(stat.ullTotalPhys / (1024 ** 3), 1)
                ram_percent = stat.dwMemoryLoad
        except Exception:
            pass


    return {
        "hostname": hostname,
        "name": hostname,
        "os": os_name,
        "cpu": cpu_cores,
        "cpu_percent": cpu_percent,
        "ram": ram_gb,
        "ram_percent": ram_percent,
        "status": "online",
        "agent": "python-background-node"
    }


def discover_server(timeout=3.0):
    """Broadcasts a UDP discovery probe to find the CyberForeSight server IP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)

    try:
        sock.sendto(MAGIC_REQUEST, ("<broadcast>", DISCOVERY_PORT))
        data, addr = sock.recvfrom(2048)
        resp = json.loads(data.decode("utf-8"))
        if resp.get("tag") == MAGIC_RESPONSE:
            server_ip = addr[0]
            port = resp.get("port", 5000)
            return f"http://{server_ip}:{port}"
    except Exception:
        pass
    finally:
        sock.close()
    return None


def send_telemetry(server_url, payload):
    """Sends JSON telemetry payload to server /device endpoint."""
    url = f"{server_url}/device"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as res:
        return res.status


def main():
    print(f"[Agent] CyberForeSight Silent Background Node started on {socket.gethostname()}")
    
    server_url = None
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        server_url = sys.argv[1].rstrip("/")

    while True:
        # Auto-discover server if not set
        if not server_url:
            print("[Agent] Searching for CyberForeSight server on local network...")
            server_url = discover_server(timeout=3.0)
            if server_url:
                print(f"[Agent] Discovered server at: {server_url}")
            else:
                # Fallback to local default if on same host
                server_url = "http://127.0.0.1:5000"

        # Collect metrics & send
        try:
            payload = get_hardware_info()
            status = send_telemetry(server_url, payload)
            # print heartbeat in quiet format
            # print(f"[Agent] Telemetry OK ({payload['hostname']} -> {server_url})")
        except Exception as e:
            # print(f"[Agent] Server unreachable at {server_url} ({e}), retrying auto-discovery...")
            server_url = None  # Re-discover next cycle

        time.sleep(6)


if __name__ == "__main__":
    main()
