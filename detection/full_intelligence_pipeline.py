from detection.intelligence_pipeline import IntelligencePipeline
from detection.explainability import Explainability
import pandas as pd


DATASET = "data/ml/cic_binary_dataset.csv"


class FullIntelligencePipeline:

    def __init__(self):

        self.intelligence = IntelligencePipeline()
        self.explainer = Explainability()

    def analyze(self, world_state):

        intelligence = self.intelligence.analyze(
            world_state
        )

        self.explainer.train_model()

        df = pd.read_csv(DATASET)

        attack_sample = df[
            df["Label"] == 1
        ].iloc[0]

        sample = attack_sample.drop(
            labels=["Label"]
        ).tolist()

        explanation = self.explainer.explain(
            sample
        )

        return {
            "intelligence": intelligence,
            "shap_explanation": explanation
        }


if __name__ == "__main__":

    pipeline = FullIntelligencePipeline()

    world_state = {

        "devices": {
            "PC-01": {
                "status": "ONLINE"
            },

            "PC-02": {
                "status": "ONLINE"
            },

            "Mobile-01": {
                "status": "ONLINE"
            }
        },

        "recent_events": [
            {
                "device": "PC-01",
                "attack": "PortScan",
                "risk": 80,
                "level": "CRITICAL"
            }
        ]
    }

    result = pipeline.analyze(world_state)

    print("\nJARVIS FULL INTELLIGENCE PIPELINE")
    print("=================================")

    print("\nFuture Prediction:")
    print(
        result["intelligence"]["future_prediction"]
    )

    print("\nK-Step Simulation:")
    print(
        result["intelligence"]["k_step_simulation"]
    )

    print("\nInfiltration Probability:")
    print(
        result["intelligence"]["infiltration_probability"]
    )

    print("\nMITRE ATT&CK:")
    print(
        result["intelligence"]["mitre_prediction"]
    )

    print("\nSHAP Explanation:")
    print(
        result["shap_explanation"]
    )