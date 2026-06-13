import os
from supabase import create_client, Client
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)

my_user_id = "f2cc9d1b-dc5d-46bb-9ee0-c6e997b24ea5" # a2soluntions@gmail.com
my_chat_id = "7155613423" # Seu Telegram Chat ID

print("Atualizando/Inserindo configurações para o seu usuário admin no Supabase...")

data = {
    "id": my_user_id,
    "telegram_chat_id": my_chat_id,
    "receive_telegram": True,
    "min_ev": 5.0,
    "banca": 1000.0,
    "alert_prematch": True,
    "alert_live": True
}

res = supabase.table("user_settings").upsert(data).execute()
print("Sucesso nas configurações:", res.data)

# Também garantir que o plano esteja como pro ou vip no profiles
profile_res = supabase.table("profiles").update({"plan": "pro"}).eq("id", my_user_id).execute()
print("Sucesso no perfil:", profile_res.data)
