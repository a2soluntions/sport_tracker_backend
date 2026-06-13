import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
vip_chat_id = os.getenv("TELEGRAM_VIP_CHAT_ID")
my_chat_id = "7155613423" # Seu Chat ID

print(f"Token: {bot_token}")
print(f"VIP Chat ID: {vip_chat_id}")
print(f"Enviando teste de link de convite para: {my_chat_id}...")

# Simular a criação do convite idêntica à do webhook
expire_date = int(time.time()) + 86400 # 24 horas
invite_url = f"https://api.telegram.org/bot{bot_token}/createChatInviteLink"
invite_payload = {
    "chat_id": vip_chat_id,
    "member_limit": 1,
    "expire_date": expire_date
}

res = requests.post(invite_url, json=invite_payload)
invite_data = res.json()

if invite_data.get("ok"):
    invite_link = invite_data["result"]["invite_link"]
    print(f"Link de convite VIP criado: {invite_link}")
    
    # Enviar a mensagem para você simulando o pagamento aprovado
    msg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    message = (
        "🏆 <b>PAGAMENTO APROVADO!</b> 🏆\n\n"
        "Seu plano <b>VIP</b> foi ativado com sucesso.\n\n"
        "Aqui está o seu link de convite exclusivo para entrar no nosso Grupo VIP de Sinais:\n"
        f"👉 <a href=\"{invite_link}\">ENTRAR NO GRUPO VIP</a>\n\n"
        "<i>(Este link expira em 24h e é válido para apenas uma entrada)</i>"
    )
    
    msg_payload = {
        "chat_id": my_chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    msg_res = requests.post(msg_url, json=msg_payload)
    print("Resposta do bot:", msg_res.json())
else:
    print("Erro ao criar link de convite:", invite_data)
