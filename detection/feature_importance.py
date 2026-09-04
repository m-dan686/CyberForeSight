import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

DATA_DIR = Path("data/cleaned")

file = next(DATA_DIR.glob("*.csv"))
df = pd.read_csv(file)

X = df.drop(columns=["Label"])
y = (df["Label"] != "BENIGN").astype(int)

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

model.fit(X, y)

importance = pd.Series(
    model.feature_importances_,
    index=X.columns
).sort_values(ascending=False)

print("\nTop 20 features:\n")
print(importance.head(20))