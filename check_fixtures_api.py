import os
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Carregar especificamente o .env.local do frontend
load_dotenv(dotenv_path="frontend/.env.local")

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = "https://v3.football.api-sports.io"

def check_fixtures():
    headers = {"x-apisports-key": API_KEY}
    tz_br = timezone(timedelta(hours=-3))
    now_br = datetime.now(tz_br)
    
    # Vamos verificar hoje e amanha
    datas = [
        now_br.strftime("%Y-%m-%d"),
        (now_br + timedelta(days=1)).strftime("%Y-%m-%d")
    ]
    
    # ID das ligas: Serie B (72), Serie C (75)
    target_leagues = ["72", "75"]
    
    print("API Key utilizada:", API_KEY)
    
    for d in datas:
        print(f"\n--- Data: {d} ---")
        url = f"{API_HOST}/fixtures"
        params = {"date": d}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            fixtures = resp.json().get("response", [])
            print(f"Total de fixtures na API para a data: {len(fixtures)}")
            matched = 0
            for f in fixtures:
                lid = str(f["league"]["id"])
                if lid in target_leagues:
                    status = f["fixture"]["status"]["short"]
                    home = f["teams"]["home"]["name"]
                    away = f["teams"]["away"]["name"]
                    round_name = f["league"]["round"]
                    f_id = f["fixture"]["id"]
                    print(f"Liga: {lid} ({f['league']['name']}) | Round: {round_name} | Jogo: {home} x {away} | Status: {status} | ID: {f_id}")
                    matched += 1
            print(f"Total encontrados Série B/C nesta data: {matched}")
        else:
            print("Erro:", resp.status_code, resp.text)

if __name__ == "__main__":
    check_fixtures()
