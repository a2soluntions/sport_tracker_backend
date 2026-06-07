import os, json, requests
from dotenv import load_dotenv
load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
try:
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    r = requests.get(url)
    data = r.json()
    with open("debug_telegram.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Updates check concluido.")
except Exception as e:
    print("Error:", e)
