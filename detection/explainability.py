import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier


DATASET = "data/ml/cic_binary_dataset.csv"


class Explainability:

    def __init__(self):
        self.model = None
        self.feature_names = None
        self.explainer = None

    def train_model(self):

        print("Loading dataset...")

        df = pd.read_csv(DATASET)

        X = df.drop(columns=["Label"])
        y = df["Label"]

        self.feature_names = X.columns.tolist()

        # Use a balanced sample
        benign = df[df["Label"] == 0].sample(
            n=5000,
            random_state=42
        )

        attack = df[df["Label"] == 1].sample(
            n=5000,
            random_state=42
        )

        train_df = pd.concat(
            [benign, attack]
        ).sample(
            frac=1,
            random_state=42
        )

        X_train = train_df.drop(columns=["Label"])
        y_train = train_df["Label"]

        print("Training model...")

        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1
        )

        self.model.fit(X_train, y_train)

        print("Creating SHAP explainer...")

        self.explainer = shap.TreeExplainer(
            self.model
        )

    def explain(self, sample):

        if self.model is None:
            self.train_model()

        sample_df = pd.DataFrame(
            [sample],
            columns=self.feature_names
        )

        prediction = self.model.predict(
            sample_df
        )[0]

        shap_values = self.explainer.shap_values(
            sample_df
        )

        # Binary classification:
        # use SHAP values for ATTACK class
        if isinstance(shap_values, list):

            values = shap_values[1][0]

        else:

            values = shap_values[0]

            if len(values.shape) > 1:
                values = values[:, 1]

        explanation = sorted(
            zip(
                self.feature_names,
                values
            ),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        top_features = []

        for feature, value in explanation[:10]:

            top_features.append({
                "feature": feature,
                "shap_value": round(
                    float(value),
                    6
                ),
                "impact": (
                    "INCREASES ATTACK RISK"
                    if value > 0
                    else "DECREASES ATTACK RISK"
                )
            })

        return {
            "prediction": int(prediction),
            "prediction_label": (
                "ATTACK"
                if prediction == 1
                else "BENIGN"
            ),
            "top_features": top_features
        }


if __name__ == "__main__":

    explainer = Explainability()

    explainer.train_model()

    df = pd.read_csv(DATASET)

    # Pick an actual attack sample
    attack_sample = df[
        df["Label"] == 1
    ].iloc[0]

    sample = attack_sample.drop(
        labels=["Label"]
    ).tolist()

    result = explainer.explain(sample)

    print("\nJARVIS SHAP EXPLAINABILITY")
    print("==========================")

    print(
        "Prediction:",
        result["prediction_label"]
    )

    print("\nTop contributing features:")

    for item in result["top_features"]:

        print(
            f"{item['feature']} -> "
            f"{item['shap_value']} "
            f"({item['impact']})"
        )