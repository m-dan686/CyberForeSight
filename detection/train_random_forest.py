import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from joblib import dump

X_train = pd.read_csv("data/ml/X_train.csv")
y_train = pd.read_csv("data/ml/y_train.csv").squeeze()

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

print("Training...")

model.fit(X_train, y_train)

dump(model, "models/random_forest.joblib")

print("Random Forest trained successfully!")
print("Model saved: models/random_forest.joblib")