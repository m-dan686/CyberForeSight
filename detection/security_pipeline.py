from risk_engine import calculate_risk

# Example real-time event
anomaly = True
attack = "DoS Hulk"
confidence = 0.98

# Risk
risk_score, risk_level = calculate_risk(
    anomaly,
    attack,
    confidence
)

print("=== JARVIS SECURITY PIPELINE ===")
print("Anomaly:", anomaly)
print("Attack:", attack)
print("Confidence:", confidence)
print("Risk Score:", risk_score)
print("Risk Level:", risk_level)

# Policy
if risk_level == "CRITICAL":
    action = "BLOCK / ISOLATE"
elif risk_level == "HIGH":
    action = "RESTRICT + ALERT"
elif risk_level == "MEDIUM":
    action = "MONITOR + ALERT"
else:
    action = "ALLOW"

print("Action:", action)