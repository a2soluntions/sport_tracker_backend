import os
import requests
import sys
from dotenv import load_dotenv

# Forçar encoding UTF-8 no print para não dar erro com emojis no Windows
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
vip_chat_id = os.getenv("TELEGRAM_VIP_CHAT_ID")
chat_id_free = os.getenv("TELEGRAM_CHAT_ID")

print(f"Token: {bot_token}")
print(f"VIP Chat ID: {vip_chat_id}")
print(f"Free Chat ID: {chat_id_free}")

def test_send(chat_id, label):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"⚽ Teste de Envio ({label})",
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload)
        print(f"Resultado {label}:", res.json())
    except Exception as e:
        print(f"Erro em {label}:", e)

print("\n--- Testando Envio para VIP ---")
test_send(vip_chat_id, "VIP")

print("\n--- Testando Envio para Free/Privado ---")
test_send(chat_id_free, "Free")
