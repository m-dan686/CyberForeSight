import chromadb
import requests

# Connect to ChromaDB
client = chromadb.PersistentClient(path="rag/chroma_db")

collection = client.get_collection(
    name="cybersecurity_knowledge"
)

# Detected attack
attack = "DoS Hulk"

# Retrieve relevant knowledge
results = collection.query(
    query_texts=[attack],
    n_results=1
)

context = results["documents"][0][0]

# Send retrieved knowledge to Qwen
prompt = f"""
You are JARVIS, a cybersecurity assistant.

Detected attack:
{attack}

Retrieved security knowledge:
{context}

Explain briefly:
1. What happened
2. Why it is risky
3. Recommended response

Use only the retrieved knowledge.
"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:7b",
        "prompt": prompt,
        "stream": False
    }
)

print("=== JARVIS RAG ===")
print(response.json()["response"])