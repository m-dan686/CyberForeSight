import pandas as pd

results = pd.DataFrame({
    "Model": ["Random Forest", "Logistic Regression"],
    "Accuracy": [0.9992868, 0.9267796],
    "Precision": [0.9975437, 0.9691890],
    "Recall": [0.9981420, 0.5752152],
    "F1 Score": [0.9978427, 0.7219512]
})

print(results.to_string(index=False))

results.to_csv("data/ml/model_comparison.csv", index=False)

print("\nSaved: data/ml/model_comparison.csv")
