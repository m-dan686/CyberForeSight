import chromadb
from pathlib import Path

client = chromadb.PersistentClient(path="rag/chroma_db")

collection = client.get_or_create_collection(
    name="cybersecurity_knowledge"
)

documents = []
ids = []

for file in Path("rag/documents").glob("*.txt"):
    documents.append(file.read_text(encoding="utf-8"))
    ids.append(file.stem)

collection.upsert(
    documents=documents,
    ids=ids
)

print("Documents loaded:", collection.count())