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

SERVER_URL = "http://172.100.128.62:5000"  # Update with Laptop 1 (Server) IP if needed


def launch_attack(target_device="Client-Laptop-2", attack_type="Infiltration / PortScan", risk=85):
    print(f"\n=======================================================")
    print(f" [!] LAUNCHING RECON & INFILTRATION ATTACK")
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

    url = f"{SERVER_URL}/security-event"
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
        print(f"[-] Could not reach server at {SERVER_URL}: {e}")
        print("    Tip: Check if Laptop 1 IP is correct and server is running.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
        SERVER_URL = sys.argv[1].rstrip("/")
    
    target = sys.argv[2] if len(sys.argv) > 2 else "Client-Laptop-2"
    launch_attack(target_device=target)
