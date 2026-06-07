import os
import requests
import json
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB_FILE = "telegram_users.json"

def enviar_alerta_telegram(confronto, campeonato, mercado, odd_oferecida, odd_justa, ev, aposta_sugerida, is_live=False, chat_id=None):
    """
    Formata e envia uma mensagem de Alerta +EV para o Telegram de um cliente específico ou de todos cadastrados.
    """
    if not TELEGRAM_BOT_TOKEN:
        print("\033[93m[!] Token do Telegram não configurado.\033[0m")
        return False

    # Determina os destinatários
    if chat_id:
        if isinstance(chat_id, (list, tuple)):
            clientes = list(chat_id)
        else:
            clientes = [chat_id]
    else:
        # Carrega a lista de clientes ativos do arquivo local
        clientes = []
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r') as f:
                    clientes = json.load(f)
            except:
                pass
                
        if not clientes:
            print("\033[93m[!] Nenhum cliente conectado no Telegram ainda. Ignorando disparo.\033[0m")
            return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Formatação Visual da Mensagem
    header = "🔴 AO VIVO - URGENTE!" if is_live else "⚽ PRÉ-JOGO ENCONTRADO!"
    
    mensagem = f"""
{header}
🏆 {campeonato}
⚔️ {confronto}

📊 Mercado: {mercado}
🎯 Odd Casa de Apostas: {odd_oferecida}
⚖️ Odd Justa (Nosso Cálculo): {odd_justa}
🔥 Vantagem (EV): +{ev:.2f}%

💰 Ação Sugerida: Apostar {aposta_sugerida}
    """

    sucesso_geral = True
    for chat_id in clientes:
        payload = {
            "chat_id": chat_id,
            "text": mensagem,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"\033[94m[OK] Sinal disparado para o Cliente ID {chat_id}!\033[0m")
            else:
                print(f"\033[31m[X] Falha ao enviar para {chat_id}: {response.text}\033[0m")
                sucesso_geral = False
        except Exception as e:
            print(f"\033[31m[X] Erro de rede no Telegram para {chat_id}: {e}\033[0m")
            sucesso_geral = False
            
    return sucesso_geral

# Bloco de Teste Independente
if __name__ == "__main__":
    print("Testando o módulo do Telegram...")
    sucesso = enviar_alerta_telegram(
        confronto="Flamengo x Palmeiras",
        campeonato="Brasileirão",
        mercado="Vitória do Flamengo",
        odd_oferecida=2.50,
        odd_justa=1.80,
        ev=15.2,
        aposta_sugerida="R$ 50.00 (5%)",
        is_live=True
    )
    if not sucesso:
        print("Lembre-se de colocar as chaves no arquivo .env!")
