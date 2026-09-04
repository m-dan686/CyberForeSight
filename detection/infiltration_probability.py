class InfiltrationProbability:

    def predict(self, world_state):

        events = world_state.get("recent_events", [])

        if not events:
            return {
                "infiltration_probability": 0,
                "risk_level": "LOW"
            }

        score = 0

        for event in events:

            attack = event.get("attack", "").lower()
            risk = event.get("risk", 0)

            if "portscan" in attack:
                score += 20

            if "dos" in attack or "ddos" in attack:
                score += 15

            if risk >= 80:
                score += 25

            elif risk >= 60:
                score += 15

        probability = min(score, 100)

        if probability >= 80:
            level = "CRITICAL"
        elif probability >= 60:
            level = "HIGH"
        elif probability >= 30:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "infiltration_probability": probability,
            "risk_level": level
        }


if __name__ == "__main__":

    predictor = InfiltrationProbability()

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

    print("\nJARVIS INFILTRATION PROBABILITY")
    print("================================")

    print(result)