import requests
import chromadb

from detection.full_intelligence_pipeline import FullIntelligencePipeline


class FullJARVIS:

    def __init__(self):

        print("JARVIS: Initializing...")

        self.pipeline = FullIntelligencePipeline()

        # Train SHAP model once
        self.pipeline.explainer.train_model()

        # Initialize RAG
        self.chroma = chromadb.PersistentClient(
            path="rag/chroma_db"
        )

        self.collection = self.chroma.get_or_create_collection(
            name="cybersecurity_knowledge"
        )

        print("JARVIS: Ready")

    # --------------------------------------------------
    # RAG
    # --------------------------------------------------

    def retrieve_knowledge(self, query):

        try:

            results = self.collection.query(
                query_texts=[query],
                n_results=2
            )

            documents = results.get("documents", [[]])[0]

            if not documents:
                return "No additional cybersecurity knowledge was found."

            return "\n\n".join(documents)

        except Exception as error:

            print("RAG ERROR:", error)

            return "No additional cybersecurity knowledge was available."

    # --------------------------------------------------
    # Ollama
    # --------------------------------------------------

    def ask_ollama(self, prompt):

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:7b",
                "prompt": prompt,
                "stream": False
            },
            timeout=300
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "response",
            "JARVIS could not generate a response."
        )

    # --------------------------------------------------
    # Voice command
    # --------------------------------------------------

    def process_voice_command(
        self,
        command,
        world_state
    ):

        print(
            "JARVIS VOICE COMMAND:",
            command
        )

        devices = world_state.get(
            "devices",
            {}
        )

        events = world_state.get(
            "recentEvents",
            []
        )

        latest_event = (
            events[-1]
            if events
            else None
        )

        device_count = len(devices)

        if latest_event:

            latest_attack = latest_event.get(
                "attack",
                "UNKNOWN"
            )

            latest_device = latest_event.get(
                "device",
                "UNKNOWN"
            )

            latest_risk = latest_event.get(
                "risk",
                0
            )

            latest_level = latest_event.get(
                "level",
                "UNKNOWN"
            )

        else:

            latest_attack = "NONE"
            latest_device = "NONE"
            latest_risk = 0
            latest_level = "LOW"

        knowledge = self.retrieve_knowledge(
            command
        )

        prompt = f"""
You are JARVIS, an AI cybersecurity assistant.

Answer the user's voice command directly.

USER COMMAND:
{command}

CURRENT SYSTEM:

Connected devices:
{device_count}

Latest security event:
Attack: {latest_attack}
Device: {latest_device}
Risk: {latest_risk}
Level: {latest_level}

Recent security events:
{events[-10:]}

Cybersecurity knowledge:
{knowledge}

Rules:

1. Answer the user's command directly.
2. Be concise.
3. Use the actual system information provided.
4. Do not invent attacks or devices.
5. If there is no security event, say so.
6. Do not claim that an anomaly is a confirmed attack unless the data says so.
7. Do not interpret simulation steps as dates.
8. Speak naturally because the answer will be converted to voice.
"""

        return self.ask_ollama(prompt)

    # --------------------------------------------------
    # Full security report
    # --------------------------------------------------

    def generate_report(
        self,
        world_state
    ):

        voice_command = world_state.get(
            "voice_command"
        )

        # If this is a voice request,
        # answer the voice command instead
        # of generating the normal report.
        if voice_command:

            response = self.process_voice_command(
                voice_command,
                world_state
            )

            return {
                "type": "voice_response",
                "command": voice_command,
                "response": response
            }

        # ---------------------------------------------
        # Normal security intelligence pipeline
        # ---------------------------------------------

        intelligence = (
            self.pipeline.intelligence.run(
                world_state
            )
        )

        events = world_state.get(
            "recentEvents",
            []
        )

        latest_event = (
            events[-1]
            if events
            else {}
        )

        attack = latest_event.get(
            "attack",
            "UNKNOWN"
        )

        # SHAP explanation
        try:

            sample = self.pipeline.explainer.get_attack_sample()

            shap_result = (
                self.pipeline.explainer.explain(
                    sample
                )
            )

        except Exception as error:

            print(
                "SHAP ERROR:",
                error
            )

            shap_result = {
                "prediction": "UNKNOWN",
                "features": []
            }

        # RAG
        knowledge = self.retrieve_knowledge(
            attack
        )

        prompt = f"""
You are JARVIS, an AI cybersecurity intelligence assistant.

Generate a concise security report.

SECURITY EVENT:
{latest_event}

INTELLIGENCE:
{intelligence}

SHAP EXPLANATION:
{shap_result}

CYBERSECURITY KNOWLEDGE:
{knowledge}

Explain:

1. What happened
2. Current risk
3. Future threat
4. Infiltration probability
5. MITRE ATT&CK stage
6. Important SHAP features
7. Recommended actions

Important:

- Do not invent facts.
- Do not treat simulation steps as dates.
- Do not claim an attack is confirmed unless the evidence supports it.
- Keep the report understandable.
"""

        report = self.ask_ollama(
            prompt
        )

        return {
            "type": "security_report",
            "attack": attack,
            "jarvis_report": report,
            "intelligence": intelligence,
            "shap": shap_result
        }


if __name__ == "__main__":

    jarvis = FullJARVIS()

    test_state = {

        "devices": {
            "PC-01": {
                "hostname": "PC-01",
                "ip": "10.157.15.10",
                "status": "ONLINE"
            }
        },

        "recentEvents": [
            {
                "device": "PC-01",
                "attack": "PortScan",
                "risk": 80,
                "level": "CRITICAL",
                "action": "MONITOR"
            }
        ],

        "voice_command":
            "What is the latest threat?"
    }

    result = jarvis.generate_report(
        test_state
    )

    print(result)