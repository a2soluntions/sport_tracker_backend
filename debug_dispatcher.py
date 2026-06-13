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

print("URL:", supabase_url)
print("Key exists:", bool(supabase_key))

supabase: Client = create_client(supabase_url, supabase_key)

# 1. Buscar perfis
profiles_resp = supabase.table("profiles").select("id, plan, role, email").execute()
print("\n--- Perfis no Supabase ---")
for p in profiles_resp.data:
    print(f"ID: {p['id']} | Email: {p['email']} | Plan: {p['plan']} | Role: {p['role']}")

# 2. Buscar configurações de usuário
settings_resp = supabase.table("user_settings").select("*").eq("receive_telegram", True).execute()
print("\n--- Configurações de Usuário no Supabase (receive_telegram=True) ---")
for s in settings_resp.data:
    print(f"ID: {s['id']} | ChatID: {s.get('telegram_chat_id')} | MinEV: {s.get('min_ev')} | Banca: {s.get('banca')}")
