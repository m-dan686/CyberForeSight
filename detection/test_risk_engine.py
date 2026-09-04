import pandas as pd
from joblib import load
from risk_engine import calculate_risk

X_test = pd.read_csv("data/ml/X_attack_test.csv")

model = load("models/attack_classifier.joblib")

X_sample = X_test.head(10)

predictions = model.predict(X_sample)
probabilities = model.predict_proba(X_sample).max(axis=1)

for attack, confidence in zip(predictions, probabilities):

    anomaly = attack != "BENIGN"

    score, level = calculate_risk(
        anomaly=anomaly,
        attack=attack,
        confidence=confidence
    )

    print(
        f"Attack: {attack} | "
        f"Confidence: {confidence:.2f} | "
        f"Risk: {score} | "
        f"Level: {level}"
    )