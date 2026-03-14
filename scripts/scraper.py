import requests
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}

def get_team_id(team_name):
    url = f"{BASE_URL}/competitions/PL/teams"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Erreur {response.status_code}: {response.text}")
        return None
    
    teams = response.json().get("teams", [])
    team = next((t for t in teams if team_name.lower() in t["name"].lower()), None)
    
    if not team:
        print(f"Équipe '{team_name}' non trouvée. Équipes disponibles :")
        for t in teams:
            print(f"  - {t['name']}")
        return None
    
    print(f"  Équipe trouvée : {team['name']} (id: {team['id']})")
    return team["id"], team["name"]

def get_team_stats(team_id, team_name):
    # Matchs récents
    url = f"{BASE_URL}/teams/{team_id}/matches?status=FINISHED&limit=10"
    response = requests.get(url, headers=HEADERS)
    matches = response.json().get("matches", []) if response.status_code == 200 else []
    
    # Infos générales équipe
    url = f"{BASE_URL}/teams/{team_id}"
    response = requests.get(url, headers=HEADERS)
    team_info = response.json() if response.status_code == 200 else {}
    
    # Classement
    url = f"{BASE_URL}/competitions/PL/standings"
    response = requests.get(url, headers=HEADERS)
    standings_data = response.json() if response.status_code == 200 else {}
    
    team_standing = None
    if standings_data:
        table = standings_data.get("standings", [{}])[0].get("table", [])
        team_standing = next((t for t in table if t["team"]["id"] == team_id), None)
    
    return {
        "team": team_name,
        "team_info": {
            "name": team_info.get("name"),
            "founded": team_info.get("founded"),
            "venue": team_info.get("venue"),
            "coach": team_info.get("coach", {}).get("name"),
        },
        "standing": team_standing,
        "recent_matches": matches
    }

def save_data(data, team_name):
    os.makedirs("data", exist_ok=True)
    filename = f"data/{team_name.lower().replace(' ', '_')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"Données sauvegardées : {filename}")

if __name__ == "__main__":
    team = sys.argv[1] if len(sys.argv) > 1 else "Arsenal"
    print(f"Scraping stats pour : {team}")
    
    result = get_team_id(team)
    if result:
        team_id, team_name = result
        data = get_team_stats(team_id, team_name)
        save_data(data, team_name)
        print("Scraping terminé avec succès !")
