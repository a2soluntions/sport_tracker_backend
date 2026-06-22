import os
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

bot_token = "8615954764:AAF0hnIVf7rlZKs7aPJy_eCP-2rX_IJi54A"
vip_chat_id = "-1003872261817"

# Vamos listar os tópicos/fóruns criados nesse chat supergroup
url_topics = f"https://api.telegram.org/bot{bot_token}/getForumTopicIconStickers"
url_chat = f"https://api.telegram.org/bot{bot_token}/getChat"

try:
    res = requests.post(url_chat, json={"chat_id": vip_chat_id})
    chat_info = res.json()
    print("Informações do Chat completo:", chat_info)
except Exception as e:
    print("Erro chat:", e)

# Tentar enviar especificando um thread_id (tópico geral costuma ser o id 1 ou id da mensagem de serviço)
# Vamos tentar enviar uma mensagem de teste para o tópico geral (geralmente message_thread_id=1 ou sem ele)
# Mas vamos testar enviar para o ID de chat direto de novo
url_send = f"https://api.telegram.org/bot{bot_token}/sendMessage"
try:
    # Teste para o Tópico Geral (ID 1)
    res = requests.post(url_send, json={"chat_id": vip_chat_id, "message_thread_id": 1, "text": "⚽ Teste no Tópico 1"})
    print("Resultado no Tópico 1:", res.json())
except Exception as e:
    print("Erro envio Tópico 1:", e)

try:
    # Teste para o Tópico Geral padrão (ID 0)
    res = requests.post(url_send, json={"chat_id": vip_chat_id, "message_thread_id": 0, "text": "⚽ Teste no Tópico 0"})
    print("Resultado no Tópico 0:", res.json())
except Exception as e:
    print("Erro envio Tópico 0:", e)
