from datetime import datetime


class WorldModel:
    def __init__(self):
        self.devices = {}
        self.events = []

    def update_device(self, device):
        hostname = device.get("hostname")

        if not hostname:
            return

        self.devices[hostname] = {
            "hostname": hostname,
            "ip": device.get("ip"),
            "os": device.get("os"),
            "cpu": device.get("cpu", 0),
            "ram": device.get("ram", 0),
            "status": device.get("status", "UNKNOWN"),
            "last_seen": datetime.now().isoformat()
        }

    def add_security_event(self, event):
        self.events.append({
            **event,
            "received_at": datetime.now().isoformat()
        })

        # Keep only recent events
        self.events = self.events[-100:]

    def get_state(self):
        return {
            "timestamp": datetime.now().isoformat(),
            "device_count": len(self.devices),
            "devices": self.devices,
            "recent_events": self.events[-20:]
        }

    def get_device(self, hostname):
        return self.devices.get(hostname)


if __name__ == "__main__":

    world = WorldModel()

    world.update_device({
        "hostname": "PC-01",
        "ip": "10.157.15.10",
        "os": "Windows",
        "cpu": 35,
        "ram": 50,
        "status": "ONLINE"
    })

    world.add_security_event({
        "device": "PC-01",
        "attack": "PortScan",
        "risk": 80,
        "level": "CRITICAL"
    })

    print("\nJARVIS WORLD MODEL")
    print("==================")

    print(world.get_state())