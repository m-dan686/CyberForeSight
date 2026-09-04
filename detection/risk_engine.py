def calculate_risk(anomaly, attack, confidence):
    if attack == "BENIGN":
        return 0, "LOW"

    score = 40

    if anomaly:
        score += 40

    if confidence >= 0.90:
        score += 20
    elif confidence >= 0.70:
        score += 10

    score = min(score, 100)

    if score >= 80:
        level = "CRITICAL"
    elif score >= 60:
        level = "HIGH"
    elif score >= 30:
        level = "MEDIUM"
    else:
        level = "LOW"

    return score, level
# Test
score, level = calculate_risk(
    anomaly=True,
    attack="PortScan",
    confidence=0.95
)

print("Risk Score:", score)
print("Risk Level:", level)