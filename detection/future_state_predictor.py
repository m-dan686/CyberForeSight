from datetime import datetime


class FutureStatePredictor:

    def __init__(self):
        self.history = []

    def record_state(self, world_state):
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "device_count": world_state.get("device_count", 0),
            "event_count": len(
                world_state.get("recent_events", [])
            )
        }

        self.history.append(snapshot)

        # Keep recent history
        self.history = self.history[-50:]

    def predict(self, world_state):

        devices = world_state.get("devices", {})
        events = world_state.get("recent_events", [])

        online_devices = sum(
            1
            for device in devices.values()
            if device.get("status") == "ONLINE"
        )

        critical_events = sum(
            1
            for event in events
            if event.get("level") == "CRITICAL"
        )

        high_events = sum(
            1
            for event in events
            if event.get("level") == "HIGH"
        )

        total_risk = sum(
            event.get("risk", 0)
            for event in events
        )

        if events:
            average_risk = total_risk / len(events)
        else:
            average_risk = 0

        # Simple future-state estimation
        if critical_events >= 3:
            predicted_state = "HIGH_THREAT"

        elif critical_events >= 1 or high_events >= 2:
            predicted_state = "ELEVATED_THREAT"

        elif events:
            predicted_state = "MONITORED"

        else:
            predicted_state = "NORMAL"

        prediction = {
            "timestamp": datetime.now().isoformat(),

            "current_state": {
                "total_devices": len(devices),
                "online_devices": online_devices,
                "recent_events": len(events),
                "critical_events": critical_events,
                "high_events": high_events,
                "average_risk": round(
                    average_risk, 2
                )
            },

            "predicted_state": predicted_state,

            "prediction_reason": (
                "Future threat state estimated "
                "from current device and security-event activity."
            )
        }

        return prediction


if __name__ == "__main__":

    predictor = FutureStatePredictor()

    world_state = {
        "device_count": 3,

        "devices": {
            "PC-01": {
                "status": "ONLINE"
            },

            "PC-02": {
                "status": "ONLINE"
            },

            "Mobile-01": {
                "status": "ONLINE"
            }
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

    predictor.record_state(world_state)

    result = predictor.predict(world_state)

    print("\nJARVIS FUTURE STATE PREDICTION")
    print("================================")

    print(result)