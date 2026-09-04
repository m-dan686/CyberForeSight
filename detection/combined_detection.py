import pandas as pd
from joblib import load
from risk_engine import calculate_risk

X_test = pd.read_csv("data/ml/X_attack_test.csv")

model = load("models/attack_classifier.joblib")

predictions = model.predict(X_test.head(20))
probabilities = model.predict_proba(X_test.head(20)).max(axis=1)

for i, (attack, confidence) in enumerate(
    zip(predictions, probabilities), start=1
):
    anomaly = attack != "BENIGN"

    score, level = calculate_risk(
        anomaly=anomaly,
        attack=attack,
        confidence=confidence
    )

    print(
        f"{i}. {attack} | "
        f"Confidence: {confidence:.2f} | "
        f"Risk: {score} | {level}"
    )