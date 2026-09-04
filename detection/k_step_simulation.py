from datetime import datetime


class KStepSimulator:

    def __init__(self, k=5):
        self.k = k

    def simulate(self, world_state):

        devices = world_state.get("devices", {})
        events = world_state.get("recent_events", [])

        critical = sum(
            1 for event in events
            if event.get("level") == "CRITICAL"
        )

        high = sum(
            1 for event in events
            if event.get("level") == "HIGH"
        )

        current_risk = sum(
            event.get("risk", 0)
            for event in events
        )

        if events:
            current_risk /= len(events)

        results = []

        risk = current_risk
        critical_events = critical
        high_events = high

        for step in range(1, self.k + 1):

            if critical_events > 0:
                risk += 5
            elif high_events > 0:
                risk += 3
            else:
                risk += 1

            risk = min(risk, 100)

            if risk >= 90:
                state = "CRITICAL"
            elif risk >= 70:
                state = "HIGH"
            elif risk >= 40:
                state = "ELEVATED"
            else:
                state = "NORMAL"

            results.append({
                "step": step,
                "predicted_risk": round(risk, 2),
                "predicted_state": state,
                "critical_events": critical_events,
                "high_events": high_events
            })

        return {
            "timestamp": datetime.now().isoformat(),
            "simulation_steps": self.k,
            "device_count": len(devices),
            "current_risk": round(current_risk, 2),
            "future_states": results
        }


if __name__ == "__main__":

    simulator = KStepSimulator(k=5)

    world_state = {
        "devices": {
            "PC-01": {"status": "ONLINE"},
            "PC-02": {"status": "ONLINE"},
            "Mobile-01": {"status": "ONLINE"}
        },

        "recent_events": [
            {
                "device": "PC-01",
                "attack": "PortScan",
                "risk": 80,
                "level": "CRITICAL"
            }
        ]
    }

    result = simulator.simulate(world_state)

    print("\nJARVIS K-STEP FORWARD SIMULATION")
    print("=================================")

    print(result)