import os
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Aqui usamos diretamente o token do bot do env
bot_token = "8615954764:AAF0hnIVf7rlZKs7aPJy_eCP-2rX_IJi54A"

# Vamos buscar informações sobre o chat VIP
# Como o ID é -1003872261817, vamos testar getChat
vip_chat_id = "-1003872261817"
url_chat = f"https://api.telegram.org/bot{bot_token}/getChat"
try:
    res = requests.post(url_chat, json={"chat_id": vip_chat_id})
    print("Informações do Chat VIP:", res.json())
except Exception as e:
    print("Erro getChat VIP:", e)

# E testar enviar mensagem simulando o payload exato
url_send = f"https://api.telegram.org/bot{bot_token}/sendMessage"
try:
    res = requests.post(url_send, json={"chat_id": vip_chat_id, "text": "⚽ Teste de Envio Simples"})
    print("Resultado envio VIP:", res.json())
except Exception as e:
    print("Erro no envio:", e)
