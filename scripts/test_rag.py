import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path=".chroma")
collection = client.get_or_create_collection(name="teams")
model = SentenceTransformer("all-MiniLM-L6-v2")

def query(question, n_results=3):
    embedding = model.encode(question).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results
    )
    print(f"\nQuestion : {question}")
    print("Résultats :")
    for doc in results["documents"][0]:
        print(f"  - {doc}")

query("Comment joue Arsenal en attaque ?")
query("Quel est le classement d'Arsenal ?")
query("Résultats récents d'Arsenal")