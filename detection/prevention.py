def prevent(device, risk_level):
    if risk_level == "CRITICAL":
        action = "BLOCK / ISOLATE"
    elif risk_level == "HIGH":
        action = "RESTRICT"
    elif risk_level == "MEDIUM":
        action = "MONITOR"
    else:
        action = "ALLOW"

    print(f"Device: {device}")
    print(f"Risk: {risk_level}")
    print(f"Action: {action}")


prevent("PC-04", "CRITICAL")