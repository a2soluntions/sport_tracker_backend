import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente do frontend/.env.local ou .env
env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_VIP_CHAT_ID = os.getenv("TELEGRAM_VIP_CHAT_ID")

if not SUPABASE_URL or not SUPABASE_KEY or not TELEGRAM_BOT_TOKEN or not TELEGRAM_VIP_CHAT_ID:
    print("\033[31m[X] Erro: Variáveis do Supabase ou Telegram ausentes no ambiente.\033[0m")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def kick_and_unban_user(telegram_chat_id, user_email):
    """
    Remove o usuário do Grupo VIP e desbane imediatamente para que possa assinar no futuro.
    """
    print(f"[-] Removendo {user_email} (ID Telegram: {telegram_chat_id}) do Grupo VIP...")
    
    # 1. Chutar do grupo
    kick_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/banChatMember"
    payload = {
        "chat_id": TELEGRAM_VIP_CHAT_ID,
        "user_id": int(telegram_chat_id),
        "revoke_messages": False
    }
    
    try:
        res = requests.post(kick_url, json=payload, timeout=10)
        if res.status_code == 200 and res.json().get("ok"):
            print(f"   [+] Usuário {telegram_chat_id} removido com sucesso.")
            
            # 2. Desbanir imediatamente para permitir futuras entradas
            unban_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/unbanChatMember"
            requests.post(unban_url, json={
                "chat_id": TELEGRAM_VIP_CHAT_ID,
                "user_id": int(telegram_chat_id),
                "only_if_banned": True
            }, timeout=10)
            
            # 3. Mandar mensagem privada avisando
            msg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(msg_url, json={
                "chat_id": telegram_chat_id,
                "text": "⚠️ <b>Sua Assinatura VIP Expirou!</b>\n\nIdentificamos que seu acesso premium ao OddsSentry Pro expirou. Por segurança, você foi removido do grupo VIP de Sinais.\n\nPara restabelecer seu acesso e voltar a receber as entradas automáticas, faça uma nova assinatura digitando /assinar.",
                "parse_mode": "HTML"
            }, timeout=10)
        else:
            print(f"   [X] Erro ao banir do Telegram: {res.text}")
    except Exception as e:
        print(f"   [X] Falha na comunicação com o Telegram: {e}")

def verificar_e_limpar_VIP():
    print(f"\n\033[96m[CLEANER] Iniciando varredura diária no Grupo VIP {TELEGRAM_VIP_CHAT_ID}...\033[0m")
    
    try:
        # 1. Buscar perfis ativos (planos pagos ou admins)
        profiles_resp = supabase.table("profiles").select("id, plan, role, email").execute()
        profiles = {p["id"]: p for p in profiles_resp.data} if profiles_resp.data else {}

        # 2. Buscar configurações de todos os usuários que conectaram Telegram
        settings_resp = supabase.table("user_settings").select("id, telegram_chat_id").execute()
        users_settings = settings_resp.data or []
        
        for user_setting in users_settings:
            telegram_chat_id = user_setting.get("telegram_chat_id")
            user_id = user_setting.get("id")
            
            if not telegram_chat_id or not telegram_chat_id.isdigit():
                continue
                
            profile = profiles.get(user_id)
            email = profile.get("email", "Desconhecido") if profile else "Desconhecido"
            
            # Verificar se o usuário é VIP ativo
            plano = profile.get("plan", "gratis") if profile else "gratis"
            role = profile.get("role", "user") if profile else "user"
            
            is_vip_active = plano in ["pro", "vip", "vitalicio"] or role in ["admin", "super_admin"]
            
            # 3. Verificar status do membro no grupo VIP do Telegram
            status_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatMember"
            try:
                res = requests.get(status_url, params={
                    "chat_id": TELEGRAM_VIP_CHAT_ID,
                    "user_id": int(telegram_chat_id)
                }, timeout=10)
                
                data = res.json()
                if data.get("ok"):
                    member_status = data["result"]["status"]
                    # Se o usuário está no grupo (como membro, administrador ou restrito)
                    if member_status in ["member", "administrator", "creator", "restricted"]:
                        if not is_vip_active:
                            # Usuário está no grupo mas NÃO tem plano ativo -> Kick!
                            kick_and_unban_user(telegram_chat_id, email)
                        else:
                            print(f"   [OK] Membro ativo validado: {email} (ID: {telegram_chat_id}) | Plano: {plano.upper()}")
                else:
                    # Se der erro (ex: usuário não está no grupo), ignoramos
                    pass
            except Exception as e:
                print(f"   [X] Erro ao checar status do membro {telegram_chat_id}: {e}")
                
        print("\033[92m[CLEANER] Varredura e limpeza concluídas!\033[0m\n")

    except Exception as e:
        print(f"\033[31m[X] Erro geral na execução do Cleaner: {e}\033[0m")

if __name__ == "__main__":
    verificar_e_limpar_VIP()
