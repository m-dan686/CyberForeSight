def decide_action(risk_level):
    if risk_level == "CRITICAL":
        return "BLOCK / ISOLATE"
    elif risk_level == "HIGH":
        return "RESTRICT + ALERT"
    elif risk_level == "MEDIUM":
        return "MONITOR + ALERT"
    else:
        return "ALLOW"


tests = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

for level in tests:
    print(level, "->", decide_action(level))