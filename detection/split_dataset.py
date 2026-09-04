import pandas as pd
from sklearn.model_selection import train_test_split

INPUT = "data/ml/cic_binary_dataset.csv"

df = pd.read_csv(INPUT)

X = df.drop(columns=["Label"])
y = df["Label"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    stratify=y,
    random_state=42
)
X_train.to_csv("data/ml/X_train.csv", index=False)
X_test.to_csv("data/ml/X_test.csv", index=False)
y_train.to_csv("data/ml/y_train.csv", index=False)
y_test.to_csv("data/ml/y_test.csv", index=False)

print("Training rows:", len(X_train))
print("Testing rows :", len(X_test))
print("Train attack ratio:", y_train.mean())
print("Test attack ratio :", y_test.mean())