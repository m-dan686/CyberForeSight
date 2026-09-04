from detection.future_state_predictor import FutureStatePredictor
from detection.k_step_simulation import KStepSimulator
from detection.infiltration_probability import InfiltrationProbability
from detection.mitre_stage_prediction import MITREStagePredictor


class IntelligencePipeline:

    def __init__(self):

        self.future_predictor = FutureStatePredictor()
        self.simulator = KStepSimulator(k=5)
        self.infiltration = InfiltrationProbability()
        self.mitre = MITREStagePredictor()

    def analyze(self, world_state):

        self.future_predictor.record_state(
            world_state
        )

        future_prediction = (
            self.future_predictor.predict(
                world_state
            )
        )

        k_step_prediction = (
            self.simulator.simulate(
                world_state
            )
        )

        infiltration = (
            self.infiltration.predict(
                world_state
            )
        )

        mitre = (
            self.mitre.predict(
                world_state
            )
        )

        return {
            "future_prediction": future_prediction,
            "k_step_simulation": k_step_prediction,
            "infiltration_probability": infiltration,
            "mitre_prediction": mitre
        }


if __name__ == "__main__":

    pipeline = IntelligencePipeline()

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

    print("\nJARVIS INTELLIGENCE PIPELINE")
    print("============================")

    print("\nFuture Prediction:")
    print(result["future_prediction"])

    print("\nK-Step Simulation:")
    print(result["k_step_simulation"])

    print("\nInfiltration:")
    print(result["infiltration_probability"])

    print("\nMITRE:")
    print(result["mitre_prediction"])