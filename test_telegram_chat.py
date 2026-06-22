import os
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Aqui usamos diretamente o token do bot do env
bot_token = "8615954764:AAF0hnIVf7rlZKs7aPJy_eCP-2rX_IJi54A"

# Vamos buscar informações sobre o bot
url_me = f"https://api.telegram.org/bot{bot_token}/getMe"
try:
    res = requests.get(url_me)
    print("Informações do Bot:", res.json())
except Exception as e:
    print("Erro getMe:", e)

# Vamos buscar informações sobre o chat VIP
# Como o ID é -1003872261817, vamos testar getChat
vip_chat_id = "-1003872261817"
url_chat = f"https://api.telegram.org/bot{bot_token}/getChat"
try:
    res = requests.post(url_chat, json={"chat_id": vip_chat_id})
    print("Informações do Chat VIP:", res.json())
except Exception as e:
    print("Erro getChat VIP:", e)

# E sobre o Chat Free
free_chat_id = "7155613423"
try:
    res = requests.post(url_chat, json={"chat_id": free_chat_id})
    print("Informações do Chat Free:", res.json())
except Exception as e:
    print("Erro getChat Free:", e)
