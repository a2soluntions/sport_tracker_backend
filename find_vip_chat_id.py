import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    # try loading from frontend/.env.local
    env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        token = os.getenv("TELEGRAM_BOT_TOKEN")

print(f"Iniciando busca do Chat ID para o bot token: {token[:15]}...")

start_time = time.time()
found = False

# Limpar updates anteriores
requests.get(f"https://api.telegram.org/bot{token}/getUpdates", params={"offset": -1})

print("Aguardando mensagem no grupo (enviar uma mensagem mencionando o bot ou comando)...")

while time.time() - start_time < 120:
    try:
        res = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", params={"timeout": 5}).json()
        if res.get("ok") and res.get("result"):
            for update in res["result"]:
                chat = None
                if "message" in update:
                    chat = update["message"]["chat"]
                    text = update["message"].get("text", "")
                    print(f"[DETECTADO] Mensagem recebida de {chat.get('title') or chat.get('username')}: '{text}' | ID: {chat.get('id')}")
                elif "my_chat_member" in update:
                    chat = update["my_chat_member"]["chat"]
                    print(f"[DETECTADO] Adicionado ao chat: {chat.get('title')} | ID: {chat.get('id')}")
                
                if chat and chat.get("id"):
                    # Se for um grupo ou supergrupo
                    if chat.get("type") in ["group", "supergroup"]:
                        print(f"\n🚀 CHAT ID DO GRUPO ENCONTRADO: {chat['id']}\n")
                        found = True
                        
                        # Salvar no .env e frontend/.env.local automaticamente
                        # 1. No .env do backend
                        env_file = ".env"
                        if os.path.exists(env_file):
                            with open(env_file, "r") as f:
                                lines = f.readlines()
                            new_lines = []
                            has_vip_id = False
                            for line in lines:
                                if line.startswith("TELEGRAM_VIP_CHAT_ID="):
                                    new_lines.append(f"TELEGRAM_VIP_CHAT_ID={chat['id']}\n")
                                    has_vip_id = True
                                else:
                                    new_lines.append(line)
                            if not has_vip_id:
                                new_lines.append(f"TELEGRAM_VIP_CHAT_ID={chat['id']}\n")
                            with open(env_file, "w") as f:
                                f.writelines(new_lines)
                            print("Atualizado .env com TELEGRAM_VIP_CHAT_ID")
                            
                        # 2. No frontend/.env.local
                        fe_env_file = os.path.join("frontend", ".env.local")
                        if os.path.exists(fe_env_file):
                            with open(fe_env_file, "r") as f:
                                lines = f.readlines()
                            new_lines = []
                            has_vip_id = False
                            for line in lines:
                                if line.startswith("TELEGRAM_VIP_CHAT_ID="):
                                    new_lines.append(f"TELEGRAM_VIP_CHAT_ID={chat['id']}\n")
                                    has_vip_id = True
                                else:
                                    new_lines.append(line)
                            if not has_vip_id:
                                new_lines.append(f"TELEGRAM_VIP_CHAT_ID={chat['id']}\n")
                            with open(fe_env_file, "w") as f:
                                f.writelines(new_lines)
                            print("Atualizado frontend/.env.local com TELEGRAM_VIP_CHAT_ID")
                            
                        break
            if found:
                break
    except Exception as e:
        print(f"Erro ao buscar updates: {e}")
    time.sleep(2)

if not found:
    print("Tempo limite de 2 minutos esgotado. Nenhuma mensagem de grupo detectada.")
else:
    print("Sucesso!")
