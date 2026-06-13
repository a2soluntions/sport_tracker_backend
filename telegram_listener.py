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
                        
                        elif texto.startswith("/assinar"):
                            msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                            payload = {
                                "chat_id": chat_id,
                                "text": "🏆 <b>Plano VIP OddsSentry</b> 🏆\n\n⚡ <b>Plano VIP Mensal</b>\n• Todos os Sinais +EV pré-jogo e ao vivo\n• Acesso ao Grupo VIP de Sinais\n• Acesso imediato após pagamento\n• <b>R$ 9,90/mês</b>",
                                "parse_mode": "HTML",
                                "reply_markup": {
                                    "inline_keyboard": [
                                        [
                                            {"text": "💎 Assinar VIP (R$ 9,90)", "callback_data": f"pay_vip_{chat_id}"},
                                        ]
                                    ]
                                }
                            }
                            requests.post(msg_url, json=payload, timeout=10)

                    elif "callback_query" in update:
                        cb_query = update["callback_query"]
                        cb_data = cb_query["data"]
                        cb_chat_id = cb_query["message"]["chat"]["id"]
                        cb_id = cb_query["id"]
                        
                        if cb_data.startswith("pay_"):
                            parts = cb_data.split("_")
                            plan_key = parts[1]
                            tg_chat_id = parts[2]
                            
                            # Notificar Telegram que recebemos o callback
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": cb_id}, timeout=10)
                            
                            try:
                                pay_url = "http://localhost:3000/api/payments/mercadopago/preference"
                                pay_payload = {
                                    "planKey": plan_key,
                                    "email": f"tg_{tg_chat_id}@oddsentry.com",
                                    "name": f"Telegram User {tg_chat_id}",
                                    "userId": f"tg_{tg_chat_id}"
                                }
                                res = requests.post(pay_url, json=pay_payload, timeout=15)
                                res_data = res.json()
                                
                                if "init_point" in res_data:
                                    init_point = res_data["init_point"]
                                    msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                                    requests.post(msg_url, json={
                                        "chat_id": cb_chat_id,
                                        "text": f"💳 <b>Fatura de Assinatura Gerada!</b>\n\nClique no link abaixo para realizar o pagamento no Mercado Pago (PIX ou Cartão):\n\n👉 <a href=\"{init_point}\">Clique aqui para Pagar</a>\n\n<i>Assim que o pagamento for confirmado, seu link de convite VIP será enviado automaticamente aqui!</i>",
                                        "parse_mode": "HTML"
                                    }, timeout=10)
                                else:
                                    msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                                    requests.post(msg_url, json={
                                        "chat_id": cb_chat_id,
                                        "text": f"❌ <b>Erro:</b> Não foi possível gerar o link de pagamento. Tente novamente mais tarde. ({res_data.get('error', 'Sem detalhes')})",
                                        "parse_mode": "HTML"
                                    }, timeout=10)
                            except Exception as e:
                                msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                                requests.post(msg_url, json={
                                    "chat_id": cb_chat_id,
                                    "text": f"❌ <b>Erro de Conexão:</b> Não foi possível conectar ao servidor de faturamento. ({str(e)})",
                                    "parse_mode": "HTML"
                                }, timeout=10)
            time.sleep(2)
        except Exception as e:
            print(f"Erro no Listener: {e}")
            time.sleep(5)

if __name__ == "__main__":
    escutar_clientes()
