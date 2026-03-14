import json
import os
import sys
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

# Initialisation
client = chromadb.PersistentClient(path=".chroma")
collection = client.get_or_create_collection(name="teams")
model = SentenceTransformer("all-MiniLM-L6-v2")

def chunk_team_data(data):
    chunks = []
    team = data.get("team", "Unknown")

    # Chunk 1 : infos générales
    info = data.get("team_info", {})
    chunks.append({
        "id": f"{team}_info",
        "text": f"{team} — entraîneur : {info.get('coach')}, stade : {info.get('venue')}, fondé en {info.get('founded')}.",
        "metadata": {"team": team, "type": "info"}
    })

    # Chunk 2 : classement
    standing = data.get("standing")
    if standing:
        chunks.append({
            "id": f"{team}_standing",
            "text": f"{team} est {standing['position']}e en Premier League avec {standing['points']} points, {standing['won']} victoires, {standing['draw']} nuls, {standing['lost']} défaites. Buts : {standing['goalsFor']} pour, {standing['goalsAgainst']} contre.",
            "metadata": {"team": team, "type": "standing"}
        })

    # Chunk 3 : matchs récents
    matches = data.get("recent_matches", [])
    for match in matches[-5:]:
        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]
        score = match.get("score", {}).get("fullTime", {})
        date = match.get("utcDate", "")[:10]
        chunks.append({
            "id": f"{team}_match_{date}",
            "text": f"Le {date} : {home} {score.get('home')} - {score.get('away')} {away}.",
            "metadata": {"team": team, "type": "match", "date": date}
        })

    return chunks

def ingest_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    team = data.get("team", "Unknown")
    print(f"Ingestion : {team}")

    chunks = chunk_team_data(data)
    print(f"  {len(chunks)} chunks générés")

    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    embeddings = model.encode(texts).tolist()

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f"  OK — ingéré dans ChromaDB")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ingest_file(sys.argv[1])
    else:
        # Ingérer tous les fichiers dans data/
        for filepath in Path("data").glob("*.json"):
            ingest_file(filepath)
    
    print(f"\nTotal dans ChromaDB : {collection.count()} chunks")