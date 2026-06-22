import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="frontend/.env.local")

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = "https://v3.football.api-sports.io"

def check_fixture_odds(fixture_id):
    headers = {"x-apisports-key": API_KEY}
    url = f"{API_HOST}/odds"
    params = {"fixture": fixture_id}
    
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 200:
        data = resp.json().get("response", [])
        if not data:
            print(f"Fixture {fixture_id}: Sem odds na API-Football.")
            return False
        
        bookmakers = data[0].get("bookmakers", [])
        names = [bm["name"] for bm in bookmakers]
        print(f"Fixture {fixture_id}: Odds encontradas! Casas: {', '.join(names)}")
        return True
    else:
        print(f"Fixture {fixture_id}: Erro API {resp.status_code}")
        return False

if __name__ == "__main__":
    # Testar algumas fixtures da Serie B/C do dia 2026-06-14 (amanhã)
    # 1520726 (Juventude x Ponte Preta)
    # 1520720 (Athletic Club x Goias)
    # 1526848 (Floresta x Figueirense)
    for f_id in [1520726, 1520720, 1526848]:
        check_fixture_odds(f_id)
