import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

banco_de_dados: Client = create_client(supabase_url, supabase_key)

def ler_configuracoes_usuario():
    """Busca a Banca e as Ligas definidas pelo usuário no Next.js"""
    try:
        resp = banco_de_dados.table('user_settings').select('*').eq('id', 1).execute()
        if resp.data and resp.data[0].get('ligas'):
            return float(resp.data[0]['banca']), resp.data[0]['ligas']
    except Exception as e:
        print(f"\033[33m[!] Aviso: Não foi possível ler configs da nuvem ({e}). Usando Banca 1000 e Ligas Padrão.\033[0m")
    
    # Busca todas as principais ligas automaticamente de forma mais precisa
    principais_ligas = [
        "https://br.betano.com/sport/futebol/brasil/brasileirao-serie-a/10016/",
        "https://br.betano.com/sport/futebol/brasil/brasileirao-serie-b/10017/",
        "https://br.betano.com/sport/futebol/inglaterra/premier-league/1/",
        "https://br.betano.com/sport/futebol/espanha/la-liga/5/",
        "https://br.betano.com/sport/futebol/italia/serie-a/15/",
        "https://br.betano.com/sport/futebol/alemanha/bundesliga/6/",
        "https://br.betano.com/sport/futebol/liga-dos-campeoes/182558/",
        "https://br.betano.com/sport/futebol/copa-libertadores/182559/",
        "https://br.betano.com/sport/futebol/copa-do-brasil/10018/"
    ]
    return 1000.0, principais_ligas

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
