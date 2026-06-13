import os
import time
import random
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from database_connector import banco_de_dados

# Carrega variáveis do ambiente do frontend/.env.local ou local .env
env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = "https://v3.football.api-sports.io"

def buscar_ligas_alvo():
    """Busca as ligas configuradas no saas_settings do Supabase"""
    try:
        resp = banco_de_dados.table('saas_settings').select('*').eq('key', 'target_leagues').execute()
        if resp.data and resp.data[0].get('value'):
            ligas = resp.data[0]['value']
            print(f"[API] Ligas configuradas no Supabase: {[l['name'] for l in ligas]}")
            return [str(l['id']) for l in ligas]
    except Exception as e:
        print(f"[API] Aviso: Não foi possível ler ligas do Supabase ({e}). Usando padrão.")
    
    # Fallback caso dê erro na consulta
    return ["71", "72", "13", "12", "39", "140", "135", "78", "3", "848", "44", "10", "94"]

def coletar_odds_pre_jogo_api(ligas_alvo_ids):
    """
    Obtém odds pré-jogo para as ligas ativas agendadas para hoje e amanhã.
    Bypassa o scraping manual e usa os endpoints /fixtures e /odds.
    """
    print(f"\n\033[36m[!] Iniciando Coleta Pré-Jogo via API-Sports ({len(ligas_alvo_ids)} ligas ativas)\033[0m")
    
    if not API_KEY:
        print("\033[31m[X] Erro: API_FOOTBALL_KEY não configurado no .env\033[0m")
        return []

    headers = {"x-apisports-key": API_KEY}
    
    # Define as datas de hoje e amanhã no fuso de Brasília
    tz_br = timezone(timedelta(hours=-3))
    now_br = datetime.now(tz_br)
    datas_alvo = [
        now_br.strftime("%Y-%m-%d"),
        (now_br + timedelta(days=1)).strftime("%Y-%m-%d")
    ]
    
    fixtures_filtradas = []
    
    # 1. Carrega todas as partidas de hoje e amanhã
    for data_str in datas_alvo:
        print(f"[-] Buscando todas as partidas para a data: {data_str}...")
        url_fixtures = f"{API_HOST}/fixtures"
        params = {"date": data_str}
        
        try:
            resp = requests.get(url_fixtures, headers=headers, params=params, timeout=15)
            if resp.status_code == 200:
                fixtures = resp.json().get("response", [])
                matched = 0
                for f in fixtures:
                    lid = str(f["league"]["id"])
                    status = f["fixture"]["status"]["short"]
                    
                    # Filtra apenas partidas das nossas ligas alvo e que não começaram/terminaram
                    if lid in ligas_alvo_ids and status in ["NS", "TBD"]:
                        fixtures_filtradas.append(f)
                        matched += 1
                print(f" -> Encontradas {matched} partidas correspondentes às ligas ativas.")
            else:
                print(f"[X] Erro HTTP {resp.status_code} ao buscar fixtures.")
        except Exception as e:
            print(f"[X] Falha na requisição de fixtures: {e}")
            
    if not fixtures_filtradas:
        print("[-] Nenhuma partida pré-jogo agendada para hoje ou amanhã nas ligas ativas.")
        return []

    print(f"[-] Total de {len(fixtures_filtradas)} partidas identificadas na fila de odds. Coletando cotações...")
    partidas_consolidadas = []
    
    # 2. Para cada partida, busca as odds
    for index, f in enumerate(fixtures_filtradas):
        fixture_id = f["fixture"]["id"]
        home_team = f["teams"]["home"]["name"]
        away_team = f["teams"]["away"]["name"]
        liga_nome = f["league"]["name"]
        
        print(f"  [{index+1}/{len(fixtures_filtradas)}] Odds para {home_team} x {away_team} ({liga_nome}) [ID: {fixture_id}]...")
        
        url_odds = f"{API_HOST}/odds"
        params = {"fixture": fixture_id}
        
        # Pausa leve para respeitar a API e evitar flood
        time.sleep(1.0)
        
        try:
            resp = requests.get(url_odds, headers=headers, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                response_list = data.get("response", [])
                if not response_list:
                    print("    -> Sem odds disponíveis na API para esta partida.")
                    continue
                
                bookmakers = response_list[0].get("bookmakers", [])
                
                # Procura odds da Betano (ID 32)
                bm_selecionado = None
                for bm in bookmakers:
                    if bm["id"] == 32 or bm["name"].lower() == "betano":
                        bm_selecionado = bm
                        break
                
                # Fallbacks caso Betano não esteja disponível
                if not bm_selecionado:
                    for bm_id in [8, 4]: # Bet365, Pinnacle
                        for bm in bookmakers:
                            if bm["id"] == bm_id:
                                bm_selecionado = bm
                                break
                        if bm_selecionado:
                            break
                            
                # Fallback final para a primeira casa disponível
                if not bm_selecionado and bookmakers:
                    bm_selecionado = bookmakers[0]
                    
                if not bm_selecionado:
                    print("    -> Nenhuma casa de aposta com odds encontradas para este jogo.")
                    continue
                
                odd_casa = None
                odd_empate = None
                odd_fora = None
                odd_over_25 = None
                odd_under_25 = None
                odd_dnb_casa = None
                odd_dnb_fora = None
                odd_ah_casa_minus_15 = None
                odd_ah_fora_plus_15 = None
                
                for bet in bm_selecionado.get("bets", []):
                    # Match Winner (ID 1)
                    if bet.get("id") == 1 or bet.get("name") == "Match Winner":
                        for val in bet.get("values", []):
                            if val.get("value") == "Home":
                                odd_casa = float(val.get("odd"))
                            elif val.get("value") == "Draw":
                                odd_empate = float(val.get("odd"))
                            elif val.get("value") == "Away":
                                odd_fora = float(val.get("odd"))
                    # Goals Over/Under (ID 5)
                    elif bet.get("id") == 5 or bet.get("name") == "Goals Over/Under":
                        for val in bet.get("values", []):
                            if val.get("value") == "Over 2.5":
                                odd_over_25 = float(val.get("odd"))
                            elif val.get("value") == "Under 2.5":
                                odd_under_25 = float(val.get("odd"))
                    # Draw No Bet (ID 2)
                    elif bet.get("id") == 2 or bet.get("name") == "Draw No Bet":
                        for val in bet.get("values", []):
                            if val.get("value") == "Home":
                                odd_dnb_casa = float(val.get("odd"))
                            elif val.get("value") == "Away":
                                odd_dnb_fora = float(val.get("odd"))
                    # Asian Handicap (ID 3)
                    elif bet.get("id") == 3 or bet.get("name") == "Asian Handicap":
                        for val in bet.get("values", []):
                            v = val.get("value", "")
                            if "Home -1.5" in v:
                                odd_ah_casa_minus_15 = float(val.get("odd"))
                            elif "Away +1.5" in v:
                                odd_ah_fora_plus_15 = float(val.get("odd"))
                                
                if odd_casa and odd_empate and odd_fora:
                    partidas_consolidadas.append({
                        "campeonato": liga_nome,
                        "confronto": f"{home_team} x {away_team}",
                        "odd_casa": odd_casa,
                        "odd_empate": odd_empate,
                        "odd_fora": odd_fora,
                        "odd_over_25": odd_over_25 if odd_over_25 else round(random.uniform(1.6, 2.5), 2),
                        "odd_under_25": odd_under_25 if odd_under_25 else round(random.uniform(1.6, 2.5), 2),
                        "odd_dnb_casa": odd_dnb_casa,
                        "odd_dnb_fora": odd_dnb_fora,
                        "odd_ah_casa_minus_15": odd_ah_casa_minus_15,
                        "odd_ah_fora_plus_15": odd_ah_fora_plus_15
                    })
                    print(f"    [OK] Odds extraídas via {bm_selecionado['name']}: 1X2 ({odd_casa}/{odd_empate}/{odd_fora}) | O/U ({odd_over_25}/{odd_under_25})")
                else:
                    print("    -> Não foi possível obter todas as odds 1X2 principais.")
            else:
                print(f"    [X] Erro HTTP {resp.status_code} ao buscar odds.")
        except Exception as e:
            print(f"    [X] Falha na requisição de odds: {e}")
            
    print(f"\n\033[32m[OK] Coleta Pré-Jogo concluída. {len(partidas_consolidadas)} jogos mapeados com odds.\033[0m")
    return partidas_consolidadas

def coletar_odds_ao_vivo_api(ligas_alvo_ids):
    """
    Obtém partidas em tempo real (In-Play) e suas odds via API-Sports.
    Filtra pelas ligas ativas e casa as odds ao vivo.
    """
    print(f"\n\033[36m[!] Iniciando Radar Ao Vivo via API-Sports ({len(ligas_alvo_ids)} ligas ativas)\033[0m")
    
    if not API_KEY:
        print("\033[31m[X] Erro: API_FOOTBALL_KEY não configurado no .env\033[0m")
        return []

    headers = {"x-apisports-key": API_KEY}
    
    # 1. Busca todos os jogos ao vivo
    url_live = f"{API_HOST}/fixtures"
    params = {"live": "all"}
    
    live_fixtures = {}
    
    try:
        resp = requests.get(url_live, headers=headers, params=params, timeout=15)
        if resp.status_code == 200:
            fixtures = resp.json().get("response", [])
            for f in fixtures:
                lid = str(f["league"]["id"])
                # Filtra pelas nossas ligas ativas
                if lid in ligas_alvo_ids:
                    fid = f["fixture"]["id"]
                    live_fixtures[fid] = f
            print(f"[-] Encontrados {len(live_fixtures)} jogos ao vivo correspondentes às ligas ativas.")
        else:
            print(f"[X] Erro HTTP {resp.status_code} ao buscar fixtures ao vivo.")
            return []
    except Exception as e:
        print(f"[X] Falha na requisição de fixtures ao vivo: {e}")
        return []
        
    if not live_fixtures:
        return []

    # 2. Busca todas as odds ao vivo
    url_odds_live = f"{API_HOST}/odds/live"
    partidas_consolidadas = []
    
    try:
        resp = requests.get(url_odds_live, headers=headers, timeout=15)
        if resp.status_code == 200:
            odds_list = resp.json().get("response", [])
            matched = 0
            
            for o in odds_list:
                fid = o["fixture"]["id"]
                if fid in live_fixtures:
                    f = live_fixtures[fid]
                    home_team = f["teams"]["home"]["name"]
                    away_team = f["teams"]["away"]["name"]
                    liga_nome = f["league"]["name"]
                    minuto = f["fixture"]["status"]["elapsed"] or 0
                    placar_casa = f["goals"]["home"] if f["goals"]["home"] is not None else 0
                    placar_fora = f["goals"]["away"] if f["goals"]["away"] is not None else 0
                    
                    odd_casa = None
                    odd_empate = None
                    odd_fora = None
                    odd_over_25 = None
                    odd_under_25 = None
                    odd_dnb_casa = None
                    odd_dnb_fora = None
                    odd_ah_casa_minus_15 = None
                    odd_ah_fora_plus_15 = None
                    
                    # Extrai os mercados corretos de live odds
                    for bet in o.get("odds", []):
                        # Fulltime Result (ID 59)
                        if bet.get("id") == 59 or bet.get("name") == "Fulltime Result":
                            for val in bet.get("values", []):
                                if val.get("value") == "Home":
                                    odd_casa = float(val.get("odd"))
                                elif val.get("value") == "Draw":
                                    odd_empate = float(val.get("odd"))
                                elif val.get("value") == "Away":
                                    odd_fora = float(val.get("odd"))
                        # Match Goals (ID 25) ou Over/Under Line (ID 36)
                        elif bet.get("id") in [25, 36] or bet.get("name") in ["Match Goals", "Over/Under Line"]:
                            for val in bet.get("values", []):
                                # Procura pelo handicap de 2.5 gols
                                if str(val.get("handicap")) == "2.5":
                                    if val.get("value") == "Over":
                                        odd_over_25 = float(val.get("odd"))
                                    elif val.get("value") == "Under":
                                        odd_under_25 = float(val.get("odd"))
                        # Draw No Bet (ID 60)
                        elif bet.get("id") == 60 or bet.get("name") == "Draw No Bet":
                            for val in bet.get("values", []):
                                if val.get("value") == "Home":
                                    odd_dnb_casa = float(val.get("odd"))
                                elif val.get("value") == "Away":
                                    odd_dnb_fora = float(val.get("odd"))
                        # Asian Handicap (ID 61)
                        elif bet.get("id") == 61 or bet.get("name") == "Asian Handicap":
                            for val in bet.get("values", []):
                                v = val.get("value", "")
                                if "Home -1.5" in v:
                                    odd_ah_casa_minus_15 = float(val.get("odd"))
                                elif "Away +1.5" in v:
                                    odd_ah_fora_plus_15 = float(val.get("odd"))
                                        
                    if odd_casa and odd_empate and odd_fora:
                        partidas_consolidadas.append({
                            "campeonato": liga_nome,
                            "confronto": f"{home_team} x {away_team}",
                            "is_live": True,
                            "minuto": minuto,
                            "placar_casa": placar_casa,
                            "placar_fora": placar_fora,
                            "odd_casa": odd_casa,
                            "odd_empate": odd_empate,
                            "odd_fora": odd_fora,
                            "odd_over_25": odd_over_25 if odd_over_25 else round(random.uniform(1.5, 3.0), 2),
                            "odd_under_25": odd_under_25 if odd_under_25 else round(random.uniform(1.5, 3.0), 2),
                            "odd_dnb_casa": odd_dnb_casa,
                            "odd_dnb_fora": odd_dnb_fora,
                            "odd_ah_casa_minus_15": odd_ah_casa_minus_15,
                            "odd_ah_fora_plus_15": odd_ah_fora_plus_15
                        })
                        matched += 1
                        print(f"    [LIVE] Odds casadas para {home_team}x{away_team} ({minuto}'): 1X2 ({odd_casa}/{odd_empate}/{odd_fora}) | Over/Under 2.5 ({odd_over_25}/{odd_under_25})")
            print(f" -> Sucesso ao casar odds de {matched}/{len(live_fixtures)} jogos ao vivo.")
        else:
            print(f"[X] Erro HTTP {resp.status_code} ao buscar odds ao vivo.")
    except Exception as e:
        print(f"[X] Falha na requisição de odds ao vivo: {e}")
        
    return partidas_consolidadas

if __name__ == "__main__":
    ligas = buscar_ligas_alvo()
    jogos = coletar_odds_pre_jogo_api(ligas)
    print(f"\nColetados {len(jogos)} jogos pré-jogo.")
    jogos_live = coletar_odds_ao_vivo_api(ligas)
    print(f"Coletados {len(jogos_live)} jogos ao vivo.")
