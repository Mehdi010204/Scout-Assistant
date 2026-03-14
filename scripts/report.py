import chromadb
import os
import sys
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = chromadb.PersistentClient(path=".chroma")
collection = client.get_or_create_collection(name="teams")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def retrieve_context(team_name, n_results=6):
    embedding = embedding_model.encode(team_name).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where={"team": team_name}
    )
    docs = results["documents"][0]
    return "\n".join(docs)

def generate_report(team_name):
    print(f"Génération du rapport tactique pour : {team_name}")
    
    context = retrieve_context(team_name)
    
    if not context:
        print("Aucune donnée trouvée pour cette équipe.")
        return None
    
    prompt = f"""Tu es un analyste tactique football expert. 
À partir des données suivantes sur {team_name}, génère un rapport tactique structuré pour préparer un match contre cette équipe.

DONNÉES :
{context}

Génère un rapport avec ces sections :
1. **Présentation générale** — forme actuelle, classement, points forts
2. **Statistiques clés** — buts marqués/encaissés, solidité défensive
3. **Résultats récents** — tendance sur les derniers matchs
4. **Points à exploiter** — faiblesses potentielles
5. **Recommandations tactiques** — comment aborder ce match

Sois précis, concis et utile pour un staff technique."""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    team = sys.argv[1] if len(sys.argv) > 1 else "Arsenal FC"
    report = generate_report(team)
    if report:
        print("\n" + "="*50)
        print(report)