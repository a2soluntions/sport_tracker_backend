import os
import re
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega variáveis do ambiente do frontend/.env.local
env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
# Usa a chave de serviço administrativa para ter permissão de escrita
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
api_football_key = os.getenv("API_FOOTBALL_KEY")

if not supabase_url or not supabase_key:
    print("\033[31m[X] Erro: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não configurados.\033[0m")
    exit(1)

if not api_football_key:
    print("\033[31m[X] Erro: API_FOOTBALL_KEY não configurado.\033[0m")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)
API_HOST = "https://v3.football.api-sports.io"

def limpar_nome_time(nome):
    """Remove espaços, acentos comuns e converte para minúsculo para comparação flexível"""
    nome = nome.lower().strip()
    # Remove tags comuns de ao vivo
    nome = re.sub(r'\[.*?\]', '', nome)
    # Remove acentos comuns
    substituicoes = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'â': 'a', 'ê': 'e', 'ô': 'o', 'ã': 'a', 'õ': 'a',
        'ç': 'c', 'ü': 'u', 'ñ': 'n'
    }
    for orig, dest in substituicoes.items():
        nome = nome.replace(orig, dest)
    return nome.strip()

def buscar_partidas_api(data_iso):
    """Busca todas as partidas da API-Football para uma determinada data (formato YYYY-MM-DD)"""
    url = f"{API_HOST}/fixtures?date={data_iso}"
    headers = {"x-apisports-key": api_football_key}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("errors") and len(data["errors"]) > 0:
                print(f"[API] Erros retornados pela API: {data['errors']}")
            return data.get("response", [])
        else:
            print(f"[API] Erro HTTP {response.status_code} ao buscar fixtures.")
    except Exception as e:
        print(f"[API] Falha de conexão: {e}")
    return []

def resolver_oportunidade(row, fixtures):
    """Analisa uma oportunidade pendente contra a lista de partidas finalizadas da API"""
    confronto = row.get("confronto", "")
    mercado = row.get("mercado", "")
    
    # Limpar confronto e separar times (ex: "Flamengo x Palmeiras")
    # Trata tags de live ex: "[LIVE|45|0-0] Flamengo x Palmeiras"
    confronto_limpo = re.sub(r'^\[.*?\]\s*', '', confronto)
    partes = confronto_limpo.split(" x ")
    if len(partes) != 2:
        print(f"[-] Formato de confronto inválido: {confronto}")
        return None, None
        
    home_previsto = limpar_nome_time(partes[0])
    away_previsto = limpar_nome_time(partes[1])
    
    # Achar o jogo correspondente nas fixtures da API
    match_found = None
    for f in fixtures:
        home_api = limpar_nome_time(f["teams"]["home"]["name"])
        away_api = limpar_nome_time(f["teams"]["away"]["name"])
        
        # Comparação flexível (se um nome contém o outro ou são muito parecidos)
        if (home_previsto in home_api or home_api in home_previsto) and \
           (away_previsto in away_api or away_api in away_previsto):
            match_found = f
            break
            
    if not match_found:
        return None, None
        
    status_api = match_found["fixture"]["status"]["short"]
    # Verificar se a partida já foi concluída
    if status_api not in ["FT", "AET", "PEN"]:
        print(f"[-] Partida {confronto} encontrada, mas ainda está com status: {status_api}")
        return None, None
        
    goals_home = match_found["goals"]["home"]
    goals_away = match_found["goals"]["away"]
    
    if goals_home is None or goals_away is None:
        return None, None
        
    placar = f"{goals_home}-{goals_away}"
    outcome = "red" # Padrão é perda, caso não satisfaça o critério
    
    # 1. Resolver Mercado de Vitória (ex: "Vitória do Flamengo")
    if "Vitoria do" in mercado or "Vitória do" in mercado or "Vencedor" in mercado:
        # Extrair time vencedor previsto
        time_vencedor_previsto = limpar_nome_time(mercado.replace("Vitória do ", "").replace("Vitoria do ", ""))
        
        if goals_home > goals_away:
            # Venceu o time da casa
            real_winner = limpar_nome_time(match_found["teams"]["home"]["name"])
            if time_vencedor_previsto in real_winner or real_winner in time_vencedor_previsto:
                outcome = "green"
        elif goals_away > goals_home:
            # Venceu o time de fora
            real_winner = limpar_nome_time(match_found["teams"]["away"]["name"])
            if time_vencedor_previsto in real_winner or real_winner in time_vencedor_previsto:
                outcome = "green"
                
    # 2. Resolver Mercado de Gols (ex: "Mais de 2.5 Gols")
    elif "Mais de 2.5" in mercado or "Over 2.5" in mercado:
        total_gols = goals_home + goals_away
        if total_gols > 2.5:
            outcome = "green"
            
    # 3. Resolver Mercado de Menos Gols (ex: "Menos de 2.5 Gols")
    elif "Menos de 2.5" in mercado or "Under 2.5" in mercado:
        total_gols = goals_home + goals_away
        if total_gols < 2.5:
            outcome = "green"
            
    print(f"\033[92m[+] Jogo {confronto} resolvido como {outcome.upper()} (Placar: {placar}) para o mercado '{mercado}'\033[0m")
    return outcome, placar

def main():
    print("="*60)
    print(" INICIANDO RESOLVEDOR AUTOMÁTICO DE RESULTADOS ".center(60, "="))
    print("="*60)
    
    # 1. Buscar oportunidades pendentes
    try:
        resp = supabase.table("ev_opportunities").select("*").eq("resultado", "pending").execute()
        pending_opps = resp.data or []
    except Exception as e:
        print(f"[X] Erro ao buscar oportunidades pendentes: {e}")
        return
        
    if not pending_opps:
        print("[-] Nenhuma oportunidade pendente encontrada no banco de dados.")
        print("="*60)
        return
        
    print(f"[-] Encontradas {len(pending_opps)} oportunidades pendentes para resolução.")
    
    # Agrupar oportunidades pendentes por data para otimizar chamadas de API
    opps_por_data = {}
    for opp in pending_opps:
        # Formato ISO date: created_at é ex '2026-05-23T20:27:23...' -> '2026-05-23'
        data_jogo = opp.get("created_at", "")[:10]
        if data_jogo:
            if data_jogo not in opps_por_data:
                opps_por_data[data_jogo] = []
            opps_por_data[data_jogo].append(opp)
            
    # Processar cada data
    for data_iso, opps in opps_por_data.items():
        print(f"\n[-] Buscando partidas da data: {data_iso}...")
        fixtures = buscar_partidas_api(data_iso)
        if not fixtures:
            print(f"[-] Nenhuma partida retornada pela API para a data {data_iso}. Pulando...")
            continue
            
        print(f"[OK] Recebidas {len(fixtures)} partidas da API. Resolvendo palpites...")
        for opp in opps:
            outcome, placar = resolver_oportunidade(opp, fixtures)
            if outcome:
                # Atualizar no Supabase
                try:
                    supabase.table("ev_opportunities").update({
                        "resultado": outcome,
                        "placar_final": placar
                    }).eq("id", opp["id"]).execute()
                except Exception as err:
                    print(f"[X] Erro ao atualizar ID {opp['id']} no Supabase: {err}")
                    
    print("\n" + "="*60)
    print(" RESOLUÇÃO DE RESULTADOS FINALIZADA ".center(60, "="))
    print("="*60)

if __name__ == "__main__":
    main()
