import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('frontend/.env.local')

url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(url, key)

print("Apagando registros pendentes de ev_opportunities...")
res = supabase.table('ev_opportunities').delete().eq('resultado', 'pending').execute()
print(f"Sucesso! Registros apagados.")
