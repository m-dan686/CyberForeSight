import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from joblib import dump

X_train = pd.read_csv("data/ml/X_train.csv")
y_train = pd.read_csv("data/ml/y_train.csv").squeeze()

model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(
        max_iter=1000,
        random_state=42
    ))
])

print("Training...")

model.fit(X_train, y_train)

dump(model, "models/logistic_regression.joblib")

print("Logistic Regression trained successfully!")