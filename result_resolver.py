import os
import re
import requests
from datetime import datetime, timedelta, timezone
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

# Cache global de fixtures por data
fixtures_cache = {}

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
    """Busca todas as partidas da API-Football para uma determinada data no fuso de Brasília"""
    url = f"{API_HOST}/fixtures?date={data_iso}&timezone=America/Sao_Paulo"
    headers = {"x-apisports-key": api_football_key}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("errors") and len(data["errors"]) > 0:
                print(f"[API] Erros retornados pela API para a data {data_iso}: {data['errors']}")
            return data.get("response", [])
        else:
            print(f"[API] Erro HTTP {response.status_code} ao buscar fixtures da data {data_iso}.")
    except Exception as e:
        print(f"[API] Falha de conexão na data {data_iso}: {e}")
    return []

def obter_fixtures_data(data_iso):
    """Retorna fixtures da data usando cache local"""
    if data_iso not in fixtures_cache:
        fixtures_cache[data_iso] = buscar_partidas_api(data_iso)
    return fixtures_cache[data_iso]

def get_brazil_date(created_at_str):
    """Converte o timestamp UTC do created_at do Supabase para a data local em formato YYYY-MM-DD (America/Sao_Paulo)"""
    try:
        # Formato esperado: '2026-06-09T01:30:00.123+00:00' ou similar
        clean_str = created_at_str.split(".")[0].replace("Z", "").split("+")[0]
        dt = datetime.strptime(clean_str[:19], "%Y-%m-%dT%H:%M:%S")
        # Subtrai 3 horas para fuso brasileiro padrão (UTC-3)
        dt_br = dt - timedelta(hours=3)
        return dt_br.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"[-] Erro ao converter data created_at ({created_at_str}): {e}")
        return created_at_str[:10]

def encontrar_partida_em_lista(home_previsto, away_previsto, fixtures):
    """Varre uma lista de fixtures tentando encontrar o confronto correspondente"""
    for f in fixtures:
        home_api = limpar_nome_time(f["teams"]["home"]["name"])
        away_api = limpar_nome_time(f["teams"]["away"]["name"])
        
        # Comparação flexível (se um nome contém o outro ou são muito parecidos)
        if (home_previsto in home_api or home_api in home_previsto) and \
           (away_previsto in away_api or away_api in away_previsto):
            return f
    return None

def resolver_oportunidade(row):
    """Analisa uma oportunidade pendente contra a lista de partidas da data correspondente (e vizinhas se necessário)"""
    confronto = row.get("confronto", "")
    mercado = row.get("mercado", "")
    created_at = row.get("created_at", "")
    
    # 1. Obter a data do jogo em fuso brasileiro (America/Sao_Paulo)
    data_br = get_brazil_date(created_at)
    
    # Limpar confronto e separar times (ex: "Flamengo x Vasco")
    confronto_limpo = re.sub(r'^\[.*?\]\s*', '', confronto)
    partes = confronto_limpo.split(" x ")
    if len(partes) != 2:
        print(f"[-] Formato de confronto inválido: {confronto}")
        return None, None
        
    home_previsto = limpar_nome_time(partes[0])
    away_previsto = limpar_nome_time(partes[1])
    
    # 2. Tentar buscar o jogo na data brasileira local (D)
    fixtures_d = obter_fixtures_data(data_br)
    match_found = encontrar_partida_em_lista(home_previsto, away_previsto, fixtures_d)
    
    # 3. Fallback: Se não achar, tenta D-1 (jogo pode ter começado no dia anterior fuso-horário)
    if not match_found:
        dt = datetime.strptime(data_br, "%Y-%m-%d")
        data_br_minus = (dt - timedelta(days=1)).strftime("%Y-%m-%d")
        fixtures_minus = obter_fixtures_data(data_br_minus)
        match_found = encontrar_partida_em_lista(home_previsto, away_previsto, fixtures_minus)
        
    # 4. Fallback: Se ainda não achar, tenta D+1 (pre-match alert feito no dia anterior)
    if not match_found:
        dt = datetime.strptime(data_br, "%Y-%m-%d")
        data_br_plus = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
        fixtures_plus = obter_fixtures_data(data_br_plus)
        match_found = encontrar_partida_em_lista(home_previsto, away_previsto, fixtures_plus)
        
    if not match_found:
        print(f"[-] Confronto '{confronto}' não encontrado nos dias vizinhos ao registro ({data_br}).")
        return None, None
        
    status_api = match_found["fixture"]["status"]["short"]
    # Se a partida foi descontinuada (cancelada, adiada, abandonada), marcamos como void
    if status_api in ["CANC", "PST", "ABD", "AWD", "WO"]:
        print(f"[-] Partida {confronto} descontinuada. Status: {status_api}. Marcando como VOID.")
        return "void", status_api

    # Verificar se a partida já foi concluída
    if status_api not in ["FT", "AET", "PEN"]:
        print(f"[-] Partida {confronto} encontrada, mas ainda não concluída. Status atual: {status_api}")
        return None, None
        
    goals_home = match_found["goals"]["home"]
    goals_away = match_found["goals"]["away"]
    
    if goals_home is None or goals_away is None:
        return None, None
        
    placar = f"{goals_home}-{goals_away}"
    outcome = "red" # Padrão é perda, caso não satisfaça o critério
    
    # 1. Resolver Mercado de Vitória (ex: "Vitória do Flamengo")
    if "Vitoria do" in mercado or "Vitória do" in mercado or "Vencedor" in mercado:
        time_vencedor_previsto = limpar_nome_time(mercado.replace("Vitória do ", "").replace("Vitoria do ", "").replace("Vencedor: ", ""))
        
        if goals_home > goals_away:
            real_winner = limpar_nome_time(match_found["teams"]["home"]["name"])
            if time_vencedor_previsto in real_winner or real_winner in time_vencedor_previsto:
                outcome = "green"
        elif goals_away > goals_home:
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
    
    # 1. Limpar registros muito antigos travados como pendentes (mais de 36 horas)
    try:
        limite_data = (datetime.now(timezone.utc) - timedelta(hours=36)).isoformat()
        resp_expired = supabase.table("ev_opportunities").update({"resultado": "expired"}).eq("resultado", "pending").lt("created_at", limite_data).execute()
        expired_count = len(resp_expired.data or []) if resp_expired.data else 0
        if expired_count > 0:
            print(f"[-] Foram expirados {expired_count} registros pendentes com mais de 36 horas.")
    except Exception as err:
        print(f"[X] Erro ao expirar registros antigos: {err}")

    # 2. Buscar as 1000 oportunidades mais recentes pendentes
    try:
        resp = supabase.table("ev_opportunities").select("*").eq("resultado", "pending").order("id", desc=True).limit(1000).execute()
        pending_opps = resp.data or []
    except Exception as e:
        print(f"[X] Erro ao buscar oportunidades pendentes: {e}")
        return
        
    if not pending_opps:
        print("[-] Nenhuma oportunidade pendente encontrada no banco de dados.")
        print("="*60)
        return
        
    print(f"[-] Encontradas {len(pending_opps)} oportunidades pendentes para resolução.")
    
    # Processar cada oportunidade com busca por vizinhança de data
    for opp in pending_opps:
        outcome, placar = resolver_oportunidade(opp)
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
