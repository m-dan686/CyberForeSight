import chromadb

client = chromadb.PersistentClient(path="rag/chroma_db")

collection = client.get_collection(
    name="cybersecurity_knowledge"
)

query = "What is DoS Hulk and how should it be handled?"

results = collection.query(
    query_texts=[query],
    n_results=1
)

print("=== JARVIS RAG RESULT ===")
print(results["documents"][0][0])