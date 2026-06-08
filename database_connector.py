import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega variables do env local ou do frontend
env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

banco_de_dados: Client = create_client(supabase_url, supabase_key)

def ler_configuracoes_usuario():
    """Busca a Banca definida pelo usuário no Next.js"""
    try:
        resp = banco_de_dados.table('user_settings').select('*').execute()
        if resp.data and len(resp.data) > 0:
            return float(resp.data[0].get('banca', 1000.0)), None
    except Exception as e:
        print(f"\033[33m[!] Aviso: Não foi possível ler configs da nuvem ({e}). Usando Banca 1000.\033[0m")
    
    return 1000.0, None

def gravar_oportunidade_ev(dados_jogo: dict, mercado_nome: str, odd_mercado: float, odd_justa: float, ev_calculado: float, texto_stake: str):
    """Grava os dados na tabela ev_opportunities"""
    registro = {
        "campeonato": dados_jogo.get("campeonato", "Desconhecido"),
        "confronto": dados_jogo.get("confronto", "Time A x Time B"),
        "mercado": mercado_nome,
        "odd_oferecida": odd_mercado,
        "odd_justa": odd_justa,
        "vantagem_ev_porcentagem": round(ev_calculado * 100, 2),
        "status_aposta": texto_stake 
    }
    
    # Executando a query
    banco_de_dados.table('ev_opportunities').insert(registro).execute()
    return True
