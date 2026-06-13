import os
import requests
import json
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    print("TOKEN_NOT_FOUND")
    exit(1)

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
try:
    res = requests.get(url, timeout=10)
    data = res.json()
    with open("scratch/updates.json", "w") as f:
        json.dump(data, f, indent=2)
    print("DUMP_OK")
except Exception as e:
    print("ERROR:", e)
