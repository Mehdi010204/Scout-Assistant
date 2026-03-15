# Scout-Assistant

A tactical analysis tool powered by RAG (Retrieval-Augmented Generation) and LLM, designed to help coaching staffs prepare for upcoming matches by generating structured scouting reports on opponent teams.

## What it does

Enter an opponent's name, get a full tactical report — current form, key stats, recent results, weaknesses to exploit, and actionable recommendations.

## Tech stack

| Layer | Tool |
|---|---|
| Data source | [football-data.org](https://www.football-data.org) API |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) |
| Vector store | ChromaDB |
| RAG pipeline | LangChain |
| LLM | Groq (LLaMA 3.3 70B) |
| Orchestration | n8n (daily auto-update workflow) |
| Interface | Streamlit + Plotly |

Everything runs locally. The only external API calls are to football-data.org (free tier) and Groq (free tier).

## Project structure

```
scout-assistant/
├── app.py                  # Streamlit interface
├── scripts/
│   ├── scraper.py          # Fetch team data from football-data.org
│   ├── ingest.py           # Chunk, embed and store in ChromaDB
│   ├── report.py           # Generate tactical report via Groq
│   └── api.py              # Flask API called by n8n
├── n8n_workflows/          # Exported n8n workflow (JSON)
├── data/                   # Scraped team data (JSON)
├── .chroma/                # ChromaDB local storage
├── .env                    # API keys (not committed)
└── requirements.txt
```

## Setup

**1. Clone the repo and create a virtual environment**
```bash
git clone https://github.com/your-username/scout-assistant.git
cd scout-assistant
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
```

**2. Set up environment variables**

Create a `.env` file at the root:
```
FOOTBALL_DATA_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

Get your free keys at:
- [football-data.org](https://www.football-data.org)
- [console.groq.com](https://console.groq.com)

**3. Scrape and ingest a team**
```bash
python scripts/scraper.py "Arsenal FC"
python scripts/ingest.py data/arsenal_fc.json
```

**4. Launch the app**
```bash
streamlit run app.py
```

## n8n automation

The `n8n_workflows/` folder contains the daily update workflow. It triggers every 24h, calls the Flask API (`scripts/api.py`) to scrape fresh data and re-ingest it into ChromaDB.

To use it:
1. Start the Flask API: `python scripts/api.py`
2. Import the workflow JSON into your local n8n instance
3. Activate the workflow

## Supported leagues

Currently configured for the **Premier League (2024/2025)**. Other leagues supported by football-data.org can be added by modifying the API calls in `scraper.py`.
