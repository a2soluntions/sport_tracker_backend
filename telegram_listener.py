import os
import time
import requests
import json
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

DB_FILE = "telegram_users.json"

def carregar_usuarios():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def salvar_usuario(chat_id):
    usuarios = carregar_usuarios()
    if chat_id not in usuarios:
        usuarios.append(chat_id)
        with open(DB_FILE, 'w') as f:
            json.dump(usuarios, f)
        return True
    return False

def escutar_clientes():
    """
    Long Polling Server: Fica perguntando ao Telegram a cada 2 segundos se alguém clicou no Link Mágico.
    Em produção, isso seria substituído por um Webhook no Next.js apontando para um domínio seguro.
    """
    print("\n\033[96m[SERVER] Servidor de Escuta do Telegram INICIADO.\033[0m")
    
    # 1. Descobrir o próprio nome para o Magic Link
    try:
        me_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        me_data = requests.get(me_url).json()
        if me_data.get("ok"):
            bot_username = me_data["result"]["username"]
            os.makedirs("frontend/public", exist_ok=True)
            with open("frontend/public/bot_info.json", "w") as f:
                json.dump({"bot_username": bot_username}, f)
            print(f"[!] Identidade Mágica confirmada: @{bot_username}")
    except Exception as e:
        print(f"Não foi possível obter username do bot: {e}")

    print("Aguardando clientes clicarem no Link Mágico no Dashboard...\n")
    
    offset = None
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset
                
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get("ok"):
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        texto = update["message"]["text"]
                        
                        # Captura o Deep Link do Telegram (ex: /start conectar)
                        if texto.startswith("/start"):
                            novo = salvar_usuario(chat_id)
                            if novo:
                                print(f"\033[92m[+] Novo Cliente Cadastrado com Sucesso! (ID: {chat_id})\033[0m")
                                # Manda mensagem de boas vindas
                                msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                                response_boas_vindas = requests.post(msg_url, json={
                                    "chat_id": chat_id,
                                    "text": "✅ <b>Conexão Estabelecida!</b>\n\nVocê agora está conectado ao <b>OddsSentry PRO</b>. A partir de agora, você receberá sinais de apostas com Valor Esperado Positivo (+EV) diretamente aqui.\n\nAguarde o radar encontrar oportunidades...",
                                    "parse_mode": "HTML"
                                })
                                if not response_boas_vindas.json().get('ok'):
                                    print("Erro ao enviar boas vindas:", response_boas_vindas.text)
            time.sleep(2)
        except Exception as e:
            print(f"Erro no Listener: {e}")
            time.sleep(5)

if __name__ == "__main__":
    escutar_clientes()
