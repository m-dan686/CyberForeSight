"""
CyberForeSight - Live Attacker Simulation Script
Run this script on the designated Attacker Laptop (Laptop 4).
It simulates an active cyber infiltration against the network / targeted client.
"""

import sys
import time
import socket
import urllib.request
import json

DISCOVERY_PORT = 5001
MAGIC_REQUEST = b"CYBERFORESIGHT_DISCOVER_SERVER"
MAGIC_RESPONSE = "CYBERFORESIGHT_SERVER_HERE"


def discover_server(timeout=2.0):
    """Broadcasts UDP probe to discover server IP automatically."""
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


def launch_attack(server_url, target_device="Client-Laptop-2", attack_type="Infiltration / PortScan", risk=85):
    print(f"\n=======================================================")
    print(f" [!] LAUNCHING RECON & INFILTRATION ATTACK")
    print(f" Server: {server_url}")
    print(f" Target: {target_device} | Attack: {attack_type}")
    print(f"=======================================================\n")

    event = {
        "device": target_device,
        "attack": attack_type,
        "risk": risk,
        "level": "CRITICAL",
        "action": "ISOLATE",
        "attacker_ip": socket.gethostbyname(socket.gethostname())
    }

    url = f"{server_url}/security-event"
    data = json.dumps(event).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            response = json.loads(res.read().decode("utf-8"))
            print(f"[*] Attack packet injected into network stream!")
            print(f"[*] Response from CyberForeSight Server: {response.get('message', 'ACK')}\n")
    except Exception as e:
        print(f"[-] Could not reach server at {server_url}: {e}")
        print("    Tip: Pass server URL explicitly e.g.: py attack_simulator.py http://192.168.137.1:5000\n")


if __name__ == "__main__":
    server_url = None
    target = "Client-Laptop-2"

    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        server_url = sys.argv[1].rstrip("/")
        if len(sys.argv) > 2:
            target = sys.argv[2]
    elif len(sys.argv) > 1:
        target = sys.argv[1]

    if not server_url:
        print("[*] Auto-discovering CyberForeSight server on network...")
        server_url = discover_server(timeout=2.0)

    if not server_url:
        # Fallback to Hotspot Gateway IP or local
        server_url = "http://192.168.137.1:5000"

    launch_attack(server_url=server_url, target_device=target)
