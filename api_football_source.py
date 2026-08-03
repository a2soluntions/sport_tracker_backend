import os
import time
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from database_connector import banco_de_dados
from api_guard import api_get, status_guard

# Carrega variáveis do ambiente do frontend/.env.local ou local .env
env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

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
    Usa api_guard.api_get() para proteção automática de cota e circuit breaker.
    """
    print(f"\n\033[36m[!] Iniciando Coleta Pré-Jogo via API-Sports ({len(ligas_alvo_ids)} ligas ativas)\033[0m")
    
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
        
        data = api_get("/fixtures", params={"date": data_str})
        if data is None:
            print(f"[Guard] Coleta bloqueada ou falhou para data {data_str}. Abortando.")
            break
        
        fixtures = data.get("response", [])
        matched = 0
        for f in fixtures:
            lid = str(f["league"]["id"])
            status = f["fixture"]["status"]["short"]
            
            # Filtra apenas partidas das nossas ligas alvo e que não começaram/terminaram
            if lid in ligas_alvo_ids and status in ["NS", "TBD"]:
                try:
                    fixture_date_str = f["fixture"]["date"]
                    fixture_time = datetime.fromisoformat(fixture_date_str.replace("Z", "+00:00"))
                    now_utc = datetime.now(timezone.utc)
                    if fixture_time <= now_utc:
                        continue
                except Exception:
                    pass
                fixtures_filtradas.append(f)
                matched += 1
        print(f" -> Encontradas {matched} partidas correspondentes às ligas ativas.")
            
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
        
        # Pausa respeitosa entre as requisições de odds
        time.sleep(1.2)
        
        data = api_get("/odds", params={"fixture": fixture_id})
        if data is None:
            print(f"    [Guard] Requisição bloqueada ou falhou. Pulando jogo.")
            continue
        
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
                    try:
                        match_date_raw = f["fixture"]["date"]
                        t_split = match_date_raw.split('T')
                        date_parts = t_split[0].split('-')
                        time_parts = t_split[1].split(':')
                        year = int(date_parts[0]); month = int(date_parts[1]); day = int(date_parts[2])
                        hour = int(time_parts[0]); minute = int(time_parts[1])
                        utc_dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
                        brt_dt = utc_dt.astimezone(timezone(timedelta(hours=-3)))
                        data_rotulo = brt_dt.strftime("%d/%m %H:%M")
                        campeonato_com_data = f"[{data_rotulo}] {liga_nome}"
                    except Exception as e:
                        print(f"    [!] Erro ao parsear data da partida: {e}")
                        campeonato_com_data = liga_nome

                    partidas_consolidadas.append({
                        "campeonato": campeonato_com_data,
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
                    print(f"    [OK] Odds extraidas via {bm_selecionado['name']}: 1X2 ({odd_casa}/{odd_empate}/{odd_fora})")
                else:
                    print("    -> Nao foi possivel obter todas as odds 1X2 principais.")
            
    print(f"\n\033[32m[OK] Coleta Pre-Jogo concluida. {len(partidas_consolidadas)} jogos mapeados com odds.\033[0m")
    # Exibe status final do guard
    s = status_guard()
    print(f"[Guard] Status final: {s['req_ultima_hora']}/{s['limite_hora']} req/hora | Circuit: {'ABERTO' if s['circuit_aberto'] else 'OK'}")
    return partidas_consolidadas

def coletar_odds_ao_vivo_api(ligas_alvo_ids):
    """
    Obtém partidas em tempo real (In-Play) e suas odds via API-Sports.
    Usa api_guard.api_get() para proteção automática.
    """
    print(f"\n\033[36m[!] Iniciando Radar Ao Vivo via API-Sports ({len(ligas_alvo_ids)} ligas ativas)\033[0m")
    
    # 1. Busca todos os jogos ao vivo
    live_fixtures = {}
    data_live = api_get("/fixtures", params={"live": "all"})
    if data_live is None:
        print("[Guard] Requisição ao vivo bloqueada ou falhou.")
        return []
    
    for f in data_live.get("response", []):
        lid = str(f["league"]["id"])
        if lid in ligas_alvo_ids:
            fid = f["fixture"]["id"]
            live_fixtures[fid] = f
    print(f"[-] Encontrados {len(live_fixtures)} jogos ao vivo correspondentes às ligas ativas.")

    if not live_fixtures:
        return []

    # 2. Busca todas as odds ao vivo
    partidas_consolidadas = []
    data_odds_live = api_get("/odds/live")
    if data_odds_live is None:
        print("[Guard] Requisição de odds ao vivo bloqueada ou falhou.")
        return []
    odds_list = data_odds_live.get("response", [])
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
            
            odd_casa = odd_empate = odd_fora = None
            odd_over_25 = odd_under_25 = None
            odd_dnb_casa = odd_dnb_fora = None
            odd_ah_casa_minus_15 = odd_ah_fora_plus_15 = None
            
            for bet in o.get("odds", []):
                if bet.get("id") == 59 or bet.get("name") == "Fulltime Result":
                    for val in bet.get("values", []):
                        if val.get("value") == "Home": odd_casa = float(val.get("odd"))
                        elif val.get("value") == "Draw": odd_empate = float(val.get("odd"))
                        elif val.get("value") == "Away": odd_fora = float(val.get("odd"))
                elif bet.get("id") in [25, 36] or bet.get("name") in ["Match Goals", "Over/Under Line"]:
                    for val in bet.get("values", []):
                        if str(val.get("handicap")) == "2.5":
                            if val.get("value") == "Over": odd_over_25 = float(val.get("odd"))
                            elif val.get("value") == "Under": odd_under_25 = float(val.get("odd"))
                elif bet.get("id") == 60 or bet.get("name") == "Draw No Bet":
                    for val in bet.get("values", []):
                        if val.get("value") == "Home": odd_dnb_casa = float(val.get("odd"))
                        elif val.get("value") == "Away": odd_dnb_fora = float(val.get("odd"))
                elif bet.get("id") == 61 or bet.get("name") == "Asian Handicap":
                    for val in bet.get("values", []):
                        v = val.get("value", "")
                        if "Home -1.5" in v: odd_ah_casa_minus_15 = float(val.get("odd"))
                        elif "Away +1.5" in v: odd_ah_fora_plus_15 = float(val.get("odd"))

            if odd_casa and odd_empate and odd_fora:
                partidas_consolidadas.append({
                    "campeonato": liga_nome, "confronto": f"{home_team} x {away_team}",
                    "is_live": True, "minuto": minuto, "placar_casa": placar_casa, "placar_fora": placar_fora,
                    "odd_casa": odd_casa, "odd_empate": odd_empate, "odd_fora": odd_fora,
                    "odd_over_25": odd_over_25 if odd_over_25 else round(random.uniform(1.5, 3.0), 2),
                    "odd_under_25": odd_under_25 if odd_under_25 else round(random.uniform(1.5, 3.0), 2),
                    "odd_dnb_casa": odd_dnb_casa, "odd_dnb_fora": odd_dnb_fora,
                    "odd_ah_casa_minus_15": odd_ah_casa_minus_15, "odd_ah_fora_plus_15": odd_ah_fora_plus_15
                })
                matched += 1
                print(f"    [LIVE] Odds casadas para {home_team}x{away_team} ({minuto}'): 1X2 ({odd_casa}/{odd_empate}/{odd_fora})")

    print(f" -> Sucesso ao casar odds de {matched}/{len(live_fixtures)} jogos ao vivo.")
    s = status_guard()
    print(f"[Guard] Status final ao vivo: {s['req_ultima_hora']}/{s['limite_hora']} req/hora")
    return partidas_consolidadas

if __name__ == "__main__":
    ligas = buscar_ligas_alvo()
    jogos = coletar_odds_pre_jogo_api(ligas)
    print(f"\nColetados {len(jogos)} jogos pré-jogo.")
    jogos_live = coletar_odds_ao_vivo_api(ligas)
    print(f"Coletados {len(jogos_live)} jogos ao vivo.")
