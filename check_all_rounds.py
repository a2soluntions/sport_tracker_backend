import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="frontend/.env.local")

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = "https://v3.football.api-sports.io"

def check_all_round_fixtures():
    headers = {"x-apisports-key": API_KEY}
    
    # Serie B: id 72, season 2026. Serie C: id 75, season 2026.
    # Vamos buscar fixtures por liga e season para ver quais jogos pertencem a essas rodadas atuais.
    for league_id, league_name in [("72", "Serie B"), ("75", "Serie C")]:
        print(f"\n=================== {league_name} ===================")
        url = f"{API_HOST}/fixtures"
        params = {"league": league_id, "season": "2026"}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            fixtures = resp.json().get("response", [])
            print(f"Total de fixtures na temporada 2026: {len(fixtures)}")
            
            # Vamos agrupar os jogos por rodada para ver os status deles
            rounds = {}
            for f in fixtures:
                r = f["league"]["round"]
                if r not in rounds:
                    rounds[r] = []
                rounds[r].append(f)
            
            # Vamos ordenar as rodadas
            for r_name in sorted(rounds.keys()):
                round_fixtures = rounds[r_name]
                # Ver quantos jogos estão pendentes, em andamento, terminados
                finished = sum(1 for f in round_fixtures if f["fixture"]["status"]["short"] == "FT")
                not_started = sum(1 for f in round_fixtures if f["fixture"]["status"]["short"] in ["NS", "TBD"])
                live = sum(1 for f in round_fixtures if f["fixture"]["status"]["short"] in ["1H", "2H", "HT", "ET", "P"])
                other = len(round_fixtures) - finished - not_started - live
                
                print(f"Rodada: {r_name} | Total: {len(round_fixtures)} | FT: {finished} | NS/TBD: {not_started} | Ao Vivo: {live} | Outros: {other}")
                
                # Se for a rodada atual (que tem jogos NS e FT misturados) ou rodadas recentes, vamos listar os jogos
                if not_started > 0 and finished > 0:
                    print("  Detalhes dos jogos desta rodada mista:")
                    for f in round_fixtures:
                        status = f["fixture"]["status"]["short"]
                        home = f["teams"]["home"]["name"]
                        away = f["teams"]["away"]["name"]
                        date = f["fixture"]["date"]
                        print(f"    - [{status}] {date} : {home} x {away} (ID: {f['fixture']['id']})")
        else:
            print("Erro:", resp.status_code, resp.text)

if __name__ == "__main__":
    check_all_round_fixtures()
