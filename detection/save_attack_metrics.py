import pandas as pd
from sklearn.metrics import classification_report

X_test = pd.read_csv("data/ml/X_attack_test.csv")
y_test = pd.read_csv("data/ml/y_attack_test.csv").squeeze()

from joblib import load

model = load("models/attack_classifier.joblib")
y_pred = model.predict(X_test)

report = classification_report(
    y_test,
    y_pred,
    output_dict=True,
    zero_division=0
)

metrics = pd.DataFrame(report).transpose()

metrics.to_csv("data/ml/attack_classification_metrics.csv")

print(metrics)
print("\nSaved: data/ml/attack_classification_metrics.csv")