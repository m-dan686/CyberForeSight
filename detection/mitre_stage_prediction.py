class MITREStagePredictor:

    def predict(self, world_state):

        events = world_state.get("recent_events", [])

        if not events:
            return {
                "stage": "UNKNOWN",
                "technique": "UNKNOWN",
                "confidence": 0
            }

        event = events[-1]

        attack = event.get("attack", "").lower()

        if "portscan" in attack:
            stage = "RECONNAISSANCE"
            technique = "T1046 - Network Service Scanning"
            confidence = 90

        elif "brute" in attack or "patator" in attack:
            stage = "CREDENTIAL ACCESS"
            technique = "T1110 - Brute Force"
            confidence = 85

        elif "dos" in attack or "ddos" in attack:
            stage = "IMPACT"
            technique = "T1498 - Network Denial of Service"
            confidence = 90

        elif "infiltration" in attack:
            stage = "COMMAND AND CONTROL"
            technique = "T1071 - Application Layer Protocol"
            confidence = 70

        else:
            stage = "UNKNOWN"
            technique = "UNKNOWN"
            confidence = 40

        return {
            "stage": stage,
            "technique": technique,
            "confidence": confidence
        }


if __name__ == "__main__":

    predictor = MITREStagePredictor()

    world_state = {
        "recent_events": [
            {
                "device": "PC-01",
                "attack": "PortScan",
                "risk": 80,
                "level": "CRITICAL"
            }
        ]
    }

    result = predictor.predict(world_state)

    print("\nJARVIS MITRE ATT&CK STAGE PREDICTION")
    print("======================================")

    print(result)