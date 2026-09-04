import requests

context = """
Attack: DoS Hulk

DoS Hulk is a denial-of-service attack that generates
a large number of HTTP requests against a target.

Risk:
It can consume server resources and reduce service availability.

Recommended response:
Monitor traffic, identify the source, rate-limit traffic,
and block the source when the attack is confirmed.
"""

prompt = f"""
You are JARVIS, a cybersecurity assistant.

Use ONLY the provided security knowledge.

Security knowledge:
{context}

Explain:
1. What happened
2. Why it is risky
3. Recommended response

Keep the answer concise.
"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:7b",
        "prompt": prompt,
        "stream": False
    }
)

print("=== JARVIS ===")
print(response.json()["response"])