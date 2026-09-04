import pandas as pd
from joblib import load
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

X_test = pd.read_csv("data/ml/X_attack_test.csv")
y_test = pd.read_csv("data/ml/y_attack_test.csv").squeeze()

model = load("models/attack_classifier.joblib")

print("Predicting...")

y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred, zero_division=0))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))