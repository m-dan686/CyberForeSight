from risk_engine import calculate_risk
from policy_engine import decide_action
from prevention import prevent

anomaly = True
attack = "DoS Hulk"
confidence = 0.98
device = "PC-04"

# Risk
risk_score, risk_level = calculate_risk(
    anomaly, attack, confidence
)

# Policy
action = decide_action(risk_level)

print("=== JARVIS DECISION PIPELINE ===")
print("Device:", device)
print("Attack:", attack)
print("Risk Score:", risk_score)
print("Risk Level:", risk_level)
print("Policy:", action)

# Prevention
prevent(device, risk_level)