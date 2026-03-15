import streamlit as st
import chromadb
import os
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv
import plotly.graph_objects as go
import plotly.express as px

load_dotenv()

st.set_page_config(
    page_title="Scout Assistant",
    page_icon="⚽",
    layout="wide"
)

@st.cache_resource
def load_models():
    client = chromadb.PersistentClient(path=".chroma")
    collection = client.get_or_create_collection(name="teams")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return collection, embedding_model, groq_client

collection, embedding_model, groq_client = load_models()

def get_available_teams():
    files = list(Path("data").glob("*.json"))
    return [f.stem.replace("_", " ").title() for f in files]

def load_team_json(team_name):
    filename = f"data/{team_name.lower().replace(' ', '_')}.json"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def retrieve_context(team_name, n_results=6):
    embedding = embedding_model.encode(team_name).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results
    )
    return "\n".join(results["documents"][0])

def generate_report(team_name, context):
    prompt = f"""Tu es un analyste tactique football expert.
À partir des données suivantes sur {team_name}, génère un rapport tactique structuré.

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

def plot_results(matches):
    results = []
    for m in matches:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        score = m.get("score", {}).get("fullTime", {})
        date = m.get("utcDate", "")[:10]
        results.append({
            "date": date,
            "match": f"{home} vs {away}",
            "home_goals": score.get("home", 0),
            "away_goals": score.get("away", 0)
        })

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[r["date"] for r in results],
        y=[r["home_goals"] for r in results],
        name="Buts domicile",
        marker_color="#1f77b4"
    ))
    fig.add_trace(go.Bar(
        x=[r["date"] for r in results],
        y=[r["away_goals"] for r in results],
        name="Buts extérieur",
        marker_color="#ff7f0e"
    ))
    fig.update_layout(
        barmode="group",
        title="Résultats récents",
        xaxis_title="Date",
        yaxis_title="Buts",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def plot_standing(standing):
    categories = ["Victoires", "Nuls", "Défaites"]
    values = [standing["won"], standing["draw"], standing["lost"]]
    colors = ["#2ecc71", "#f39c12", "#e74c3c"]

    fig = go.Figure(go.Pie(
        labels=categories,
        values=values,
        marker_colors=colors,
        hole=0.4
    ))
    fig.update_layout(
        title="Répartition des résultats",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig

# --- UI ---
st.title("⚽ Scout Assistant")
st.markdown("*Analyse tactique alimentée par RAG + LLM*")

st.sidebar.header("🔍 Sélection de l'équipe")
teams = get_available_teams()

if not teams:
    st.warning("Aucune équipe dans la base. Lance d'abord le scraper.")
    st.stop()

selected_team = st.sidebar.selectbox("Équipe adverse", teams)

if st.sidebar.button("Générer le rapport", type="primary"):
    data = load_team_json(selected_team)

    if not data:
        st.error("Données non trouvées pour cette équipe.")
        st.stop()

    # Infos générales
    col1, col2, col3, col4 = st.columns(4)
    standing = data.get("standing", {})
    if standing:
        col1.metric("Position", f"{standing.get('position')}e")
        col2.metric("Points", standing.get("points"))
        col3.metric("Buts marqués", standing.get("goalsFor"))
        col4.metric("Buts encaissés", standing.get("goalsAgainst"))

    st.divider()

    # Visualisations
    col_left, col_right = st.columns(2)

    with col_left:
        matches = data.get("recent_matches", [])
        if matches:
            st.plotly_chart(plot_results(matches), use_container_width=True)

    with col_right:
        if standing:
            st.plotly_chart(plot_standing(standing), use_container_width=True)

    st.divider()

    # Rapport tactique
    st.subheader("📋 Rapport tactique")
    with st.spinner("Génération du rapport..."):
        context = retrieve_context(selected_team)
        report = generate_report(selected_team, context)
        st.markdown(report)