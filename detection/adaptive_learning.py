import pandas as pd

df = pd.read_csv("data/ml/cic_ml_dataset.csv")

feature = "Fwd Packet Length Mean"

values = df[feature].replace(
    [float("inf"), -float("inf")], 0
).fillna(0)

old_mean = values.iloc[:10000].mean()
new_mean = values.iloc[-10000:].mean()

difference = abs(new_mean - old_mean)

print("Old mean:", round(old_mean, 2))
print("New mean:", round(new_mean, 2))
print("Mean difference:", round(difference, 2))

if difference > old_mean * 0.20:
    print("⚠️ Concept drift detected")
    
    # Update baseline
    updated_baseline = new_mean
    
    print("🔄 Baseline updated to:", round(updated_baseline, 2))
else:
    print("✅ No significant concept drift")