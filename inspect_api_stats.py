import os
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
load_dotenv(env_path)

API_KEY = os.getenv("API_FOOTBALL_KEY")
headers = {"x-apisports-key": API_KEY}
API_HOST = "https://v3.football.api-sports.io"

# Testar buscando estatísticas do Flamengo (ID 127) na Série A (ID 71) em 2026 (ou 2024 se não iniciado)
url = f"{API_HOST}/teams/statistics"
params = {
    "league": "71",
    "season": "2024",
    "team": "127"
}

resp = requests.get(url, headers=headers, params=params)
data = resp.json()
print("response keys:", data.keys())
if data.get("response"):
    stats = data["response"]
    print("Cards stats:", stats.get("cards"))
    # Algumas ligas têm estatísticas de escanteios (corners) ou não
    print("Outros dados disponíveis:")
    for key in stats:
        if isinstance(stats[key], dict):
            print(f"- {key}: {list(stats[key].keys())[:5]}")
        else:
            print(f"- {key}")
else:
    print("Sem resposta da API:", data)
