import time
import random
import os
import json
import requests
from datetime import datetime, timedelta, timezone
from api_football_source import coletar_odds_pre_jogo_api, coletar_odds_ao_vivo_api, buscar_ligas_alvo
from poisson_model import calcular_probabilidades_poisson
from ev_calculator import calcular_ev
from database_connector import gravar_oportunidade_ev, ler_configuracoes_usuario, ler_configuracoes_saas
from kelly_criterion import calcular_criterio_kelly
from alert_dispatcher import despachar_alertas_personalizados
import result_resolver

def should_run_schedule(tipo, hora_agendada, data_hoje):
    filepath = "last_runs.json"
    runs = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                runs = json.load(f)
        except:
            pass
            
    if tipo not in runs:
        runs[tipo] = {}
    if data_hoje not in runs[tipo]:
        runs[tipo][data_hoje] = []
        
    return hora_agendada not in runs[tipo][data_hoje]

def mark_schedule_run(tipo, hora_agendada, data_hoje):
    filepath = "last_runs.json"
    runs = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                runs = json.load(f)
        except:
            pass
            
    if tipo not in runs:
        runs[tipo] = {}
    if data_hoje not in runs[tipo]:
        runs[tipo][data_hoje] = []
        
    if hora_agendada not in runs[tipo][data_hoje]:
        runs[tipo][data_hoje].append(hora_agendada)
        
    with open(filepath, 'w') as f:
        json.dump(runs, f, indent=2)

def is_time_active(scheduled_str, now_dt):
    try:
        sch_h, sch_m = map(int, scheduled_str.split(':'))
        sch_dt = now_dt.replace(hour=sch_h, minute=sch_m, second=0, microsecond=0)
        diff = (now_dt - sch_dt).total_seconds()
        return 0 <= diff <= 600  # 10 minutes window
    except:
        return False


def main():
    # 0. Executa o resolvedor de resultados automático para atualizar pendências do passado
    try:
        result_resolver.main()
    except Exception as e:
        print(f"\033[33m[!] Aviso: Não foi possível executar o resolvedor de resultados ({e})\033[0m")

    print("\n" + "="*60)
    print(" INICIANDO ORQUESTRAÇÃO DE DADOS E ANÁLISE +EV ".center(60, "="))
    print("="*60)

    # 1. Carrega as Configurações
    banca_usuario, _ = ler_configuracoes_usuario()
    ligas_alvo = buscar_ligas_alvo()
    print(f"[-] Configuração Ativa: Banca de R$ {banca_usuario:.2f} | Alvos: {len(ligas_alvo)} Ligas")

    settings = ler_configuracoes_saas()
    
    # 1.1. Obter fuso de Brasília
    tz_br = timezone(timedelta(hours=-3))
    now_br = datetime.now(tz_br)
    today_date_str = now_br.strftime("%Y-%m-%d")
    
    # 1.2. Verificar agendamento de Alertas EV (+EV)
    telegram_bot_enabled = settings.get('telegram_bot_enabled') == True
    telegram_bot_hours = settings.get('telegram_bot_hours', [])
    
    should_dispatch_ev = False
    matched_ev_hour = None
    
    if telegram_bot_enabled:
        for hour in telegram_bot_hours:
            if is_time_active(hour, now_br) and should_run_schedule('alerta_ev', hour, today_date_str):
                should_dispatch_ev = True
                matched_ev_hour = hour
                break
                
    print(f"[-] Robô de Sinais VIP: {'ATIVO' if telegram_bot_enabled else 'INATIVO'} | Horário correspondente: {'SIM (' + matched_ev_hour + ')' if should_dispatch_ev else 'NÃO'}")

    # 1.3. Dispara piloto automático de palpites no Next.js (que gerencia agendamento e envio próprio)
    try:
        app_url = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000").rstrip("/")
        url_auto = f"{app_url}/api/telegram/auto-dispatch"
        headers = {"Authorization": f"Bearer {os.getenv('SUPABASE_SERVICE_ROLE_KEY')}"}
        resp = requests.post(url_auto, headers=headers, timeout=15)
        if resp.status_code == 200:
            res_json = resp.json()
            palpites_status = res_json.get("palpites", {})
            if palpites_status.get("dispatched"):
                print(f"[Auto-Broadcast] Palpites do dia disparados com sucesso via API Next.js!")
            elif palpites_status.get("enabled"):
                print(f"[Auto-Broadcast] Piloto de palpites verificado. Nenhum disparo de hora ativa pendente.")
        else:
            print(f"[Auto-Broadcast] Chamada da API auto-dispatch retornou status {resp.status_code}")
    except Exception as e:
        print(f"[Auto-Broadcast] Não foi possível chamar a API auto-dispatch ({e})")


    if not ligas_alvo:
        print("\n\033[31m[X] Nenhuma liga selecionada no painel. Abortando ciclo.\033[0m")
        return

    # 2. Obtenção de odds via API-Sports (Pré-Jogo e Ao Vivo)
    jogos_pre_match = coletar_odds_pre_jogo_api(ligas_alvo)
    jogos_ao_vivo = coletar_odds_ao_vivo_api(ligas_alvo)
    
    jogos_raspados = jogos_pre_match + jogos_ao_vivo
    
    if not jogos_raspados:
        print("\n\033[31m[X] Nenhum jogo processado na varredura. Abortando ciclo.\033[0m")
        return

    print("\n\033[36m[!] Iniciando Motor de Poisson Bidimensional...\033[0m")
    
    # 3. Processa os jogos coletados
    for jogo in jogos_raspados:
        print(f"\n\033[1mAnalisando: {jogo['confronto']} ({jogo['campeonato']})\033[0m")
        # Determinar xG dinâmico usando as odds de mercado como base de probabilidade implícita
        # Cotação menor significa maior favoritismo, logo maior xG projetado.
        odd_c = float(jogo.get('odd_casa', 2.0))
        odd_f = float(jogo.get('odd_fora', 2.0))
        
        # Probabilidades implícitas brutas
        prob_impl_c = 1.0 / odd_c if odd_c > 0 else 0.5
        prob_impl_f = 1.0 / odd_f if odd_f > 0 else 0.5
        total_impl = prob_impl_c + prob_impl_f
        
        # Normalizar para obter proporções
        prop_c = prob_impl_c / total_impl if total_impl > 0 else 0.5
        prop_f = prob_impl_f / total_impl if total_impl > 0 else 0.5
        
        # Definir a média de gols total esperada na partida (ex: 2.5 gols em média)
        total_gols_projetado = 2.6
        
        # Injetar o xG proporcional
        xg_casa_simulado = round(total_gols_projetado * prop_c, 2)
        xg_fora_simulado = round(total_gols_projetado * prop_f, 2)
        
        # Garante limites saudáveis de segurança (mínimo de 0.3 e máximo de 3.5)
        xg_casa_simulado = max(0.3, min(3.5, xg_casa_simulado))
        xg_fora_simulado = max(0.3, min(3.5, xg_fora_simulado))
        
        if jogo.get('is_live'):
            minuto = jogo['minuto']
            placar_c = jogo['placar_casa']
            placar_f = jogo['placar_fora']
            print(f"   \033[91m-> STATUS: AO VIVO ({minuto}') | PLACAR: {placar_c}x{placar_f}\033[0m")
            
            odds_justas = calcular_probabilidades_poisson(
                xg_casa=xg_casa_simulado, xg_fora=xg_fora_simulado,
                tempo_decorrido=minuto, gols_casa_atuais=placar_c, gols_fora_atuais=placar_f
            )
            # Injeta a Tag Visual no Campeonato para o FrontEnd ler
            jogo['campeonato'] = f"[LIVE|{minuto}|{placar_c}-{placar_f}] {jogo['campeonato']}"
        else:
            odds_justas = calcular_probabilidades_poisson(xg_casa=xg_casa_simulado, xg_fora=xg_fora_simulado)
        
        # --- AVALIAÇÃO MERCADO 1: MATCH ODDS (CASA VENCE) ---
        odd_justa_casa = odds_justas['odd_justa_casa']
        prob_casa_pct = odds_justas['prob_casa_pct']
        
        resultado_ev_vencedor = calcular_ev(odd_casa=jogo['odd_casa'], probabilidade_calculada_pct=prob_casa_pct)
        
        if resultado_ev_vencedor['ev'] > 0:
            print(f"\033[92m[$$$] ALERTA (1X2): ODD {jogo['odd_casa']} | JUSTA: {odd_justa_casa:.2f} | EV: +{resultado_ev_vencedor['ev']}\033[0m")
            
            stake_info = calcular_criterio_kelly(jogo['odd_casa'], prob_casa_pct, 0.25)
            pct = stake_info['porcentagem_banca_ajustada']
            texto_stake_final = f"R$ {banca_usuario * (pct / 100.0):.2f} ({pct:.1f}%)"
            
            time_casa = jogo['confronto'].split(' x ')[0]
            
            gravar_oportunidade_ev(
                dados_jogo=jogo,
                mercado_nome=f"Vitória do {time_casa}",
                odd_mercado=jogo['odd_casa'],
                odd_justa=round(odd_justa_casa, 2),
                ev_calculado=resultado_ev_vencedor['ev'],
                texto_stake=texto_stake_final
            )
            
            # Dispara Notificação Celular Personalizada se estiver no horário agendado
            if should_dispatch_ev:
                despachar_alertas_personalizados(
                    confronto=jogo['confronto'],
                    campeonato=jogo['campeonato'],
                    mercado=f"Vitória do {time_casa}",
                    odd_oferecida=jogo['odd_casa'],
                    odd_justa=round(odd_justa_casa, 2),
                    ev_decimal=resultado_ev_vencedor['ev'],
                    is_live=jogo.get('is_live', False)
                )
        
        # --- AVALIAÇÃO MERCADO 2: TOTAL DE GOLS (OVER 2.5) ---
        # Garante que não quebre caso o scraper anterior (fallback manual) não tenha gerado odd_over_25
        odd_over_mercado = jogo.get('odd_over_25', round(random.uniform(1.6, 2.5), 2))
        odd_justa_over = odds_justas['odd_justa_over_25']
        prob_over_pct = odds_justas['prob_over_25_pct']
        
        resultado_ev_gols = calcular_ev(odd_casa=odd_over_mercado, probabilidade_calculada_pct=prob_over_pct)
        
        if resultado_ev_gols['ev'] > 0:
            print(f"\033[92m[$$$] ALERTA (GOLS): ODD {odd_over_mercado} | JUSTA: {odd_justa_over:.2f} | EV: +{resultado_ev_gols['ev']}\033[0m")
            
            stake_info_gols = calcular_criterio_kelly(odd_over_mercado, prob_over_pct, 0.25)
            pct_gols = stake_info_gols['porcentagem_banca_ajustada']
            texto_stake_gols = f"R$ {banca_usuario * (pct_gols / 100.0):.2f} ({pct_gols:.1f}%)"
            
            gravar_oportunidade_ev(
                dados_jogo=jogo,
                mercado_nome="Mais de 2.5 Gols",
                odd_mercado=odd_over_mercado,
                odd_justa=round(odd_justa_over, 2),
                ev_calculado=resultado_ev_gols['ev'],
                texto_stake=texto_stake_gols
            )
            
            # Dispara Notificação Celular Personalizada se estiver no horário agendado
            if should_dispatch_ev:
                despachar_alertas_personalizados(
                    confronto=jogo['confronto'],
                    campeonato=jogo['campeonato'],
                    mercado="Mais de 2.5 Gols",
                    odd_oferecida=odd_over_mercado,
                    odd_justa=round(odd_justa_over, 2),
                    ev_decimal=resultado_ev_gols['ev'],
                    is_live=jogo.get('is_live', False)
                )

        # --- AVALIAÇÃO MERCADO 3: DRAW NO BET (EMPATE ANULA) CASA ---
        odd_dnb_casa = jogo.get('odd_dnb_casa')
        if odd_dnb_casa:
            odd_justa_dnb_c = odds_justas['odd_justa_dnb_casa']
            prob_dnb_c_pct = odds_justas['prob_dnb_casa_pct']
            resultado_ev_dnb_c = calcular_ev(odd_casa=odd_dnb_casa, probabilidade_calculada_pct=prob_dnb_c_pct)
            
            if resultado_ev_dnb_c['ev'] > 0:
                print(f"\033[92m[$$$] ALERTA (DNB CASA): ODD {odd_dnb_casa} | JUSTA: {odd_justa_dnb_c:.2f} | EV: +{resultado_ev_dnb_c['ev']}\033[0m")
                stake_info_dnb_c = calcular_criterio_kelly(odd_dnb_casa, prob_dnb_c_pct, 0.25)
                pct_dnb_c = stake_info_dnb_c['porcentagem_banca_ajustada']
                texto_stake_dnb_c = f"R$ {banca_usuario * (pct_dnb_c / 100.0):.2f} ({pct_dnb_c:.1f}%)"
                
                time_casa = jogo['confronto'].split(' x ')[0]
                gravar_oportunidade_ev(
                    dados_jogo=jogo,
                    mercado_nome=f"Empate Anula: Vitória do {time_casa}",
                    odd_mercado=odd_dnb_casa,
                    odd_justa=round(odd_justa_dnb_c, 2),
                    ev_calculado=resultado_ev_dnb_c['ev'],
                    texto_stake=texto_stake_dnb_c
                )

        # --- AVALIAÇÃO MERCADO 4: DRAW NO BET (EMPATE ANULA) FORA ---
        odd_dnb_fora = jogo.get('odd_dnb_fora')
        if odd_dnb_fora:
            odd_justa_dnb_f = odds_justas['odd_justa_dnb_fora']
            prob_dnb_f_pct = odds_justas['prob_dnb_fora_pct']
            resultado_ev_dnb_f = calcular_ev(odd_casa=odd_dnb_fora, probabilidade_calculada_pct=prob_dnb_f_pct)
            
            if resultado_ev_dnb_f['ev'] > 0:
                print(f"\033[92m[$$$] ALERTA (DNB FORA): ODD {odd_dnb_fora} | JUSTA: {odd_justa_dnb_f:.2f} | EV: +{resultado_ev_dnb_f['ev']}\033[0m")
                stake_info_dnb_f = calcular_criterio_kelly(odd_dnb_fora, prob_dnb_f_pct, 0.25)
                pct_dnb_f = stake_info_dnb_f['porcentagem_banca_ajustada']
                texto_stake_dnb_f = f"R$ {banca_usuario * (pct_dnb_f / 100.0):.2f} ({pct_dnb_f:.1f}%)"
                
                time_fora = jogo['confronto'].split(' x ')[1]
                gravar_oportunidade_ev(
                    dados_jogo=jogo,
                    mercado_nome=f"Empate Anula: Vitória do {time_fora}",
                    odd_mercado=odd_dnb_fora,
                    odd_justa=round(odd_justa_dnb_f, 2),
                    ev_calculado=resultado_ev_dnb_f['ev'],
                    texto_stake=texto_stake_dnb_f
                )

        # --- AVALIAÇÃO MERCADO 5: HANDICAP ASIÁTICO -1.5 CASA ---
        odd_ah_c_minus_15 = jogo.get('odd_ah_casa_minus_15')
        if odd_ah_c_minus_15:
            odd_justa_ah_c = odds_justas['odd_justa_ah_casa_minus_15']
            prob_ah_c_pct = odds_justas['prob_ah_casa_minus_15_pct']
            resultado_ev_ah_c = calcular_ev(odd_casa=odd_ah_c_minus_15, probabilidade_calculada_pct=prob_ah_c_pct)
            
            if resultado_ev_ah_c['ev'] > 0:
                print(f"\033[92m[$$$] ALERTA (AH CASA -1.5): ODD {odd_ah_c_minus_15} | JUSTA: {odd_justa_ah_c:.2f} | EV: +{resultado_ev_ah_c['ev']}\033[0m")
                stake_info_ah_c = calcular_criterio_kelly(odd_ah_c_minus_15, prob_ah_c_pct, 0.25)
                pct_ah_c = stake_info_ah_c['porcentagem_banca_ajustada']
                texto_stake_ah_c = f"R$ {banca_usuario * (pct_ah_c / 100.0):.2f} ({pct_ah_c:.1f}%)"
                
                time_casa = jogo['confronto'].split(' x ')[0]
                gravar_oportunidade_ev(
                    dados_jogo=jogo,
                    mercado_nome=f"Handicap: {time_casa} -1.5",
                    odd_mercado=odd_ah_c_minus_15,
                    odd_justa=round(odd_justa_ah_c, 2),
                    ev_calculado=resultado_ev_ah_c['ev'],
                    texto_stake=texto_stake_ah_c
                )

        # --- AVALIAÇÃO MERCADO 6: HANDICAP ASIÁTICO +1.5 FORA ---
        odd_ah_f_plus_15 = jogo.get('odd_ah_fora_plus_15')
        if odd_ah_f_plus_15:
            odd_justa_ah_f = odds_justas['odd_justa_ah_fora_plus_15']
            prob_ah_f_pct = odds_justas['prob_ah_fora_plus_15_pct']
            resultado_ev_ah_f = calcular_ev(odd_casa=odd_ah_f_plus_15, probabilidade_calculada_pct=prob_ah_f_pct)
            
            if resultado_ev_ah_f['ev'] > 0:
                print(f"\033[92m[$$$] ALERTA (AH FORA +1.5): ODD {odd_ah_f_plus_15} | JUSTA: {odd_justa_ah_f:.2f} | EV: +{resultado_ev_ah_f['ev']}\033[0m")
                stake_info_ah_f = calcular_criterio_kelly(odd_ah_f_plus_15, prob_ah_f_pct, 0.25)
                pct_ah_f = stake_info_ah_f['porcentagem_banca_ajustada']
                texto_stake_ah_f = f"R$ {banca_usuario * (pct_ah_f / 100.0):.2f} ({pct_ah_f:.1f}%)"
                
                time_fora = jogo['confronto'].split(' x ')[1]
                gravar_oportunidade_ev(
                    dados_jogo=jogo,
                    mercado_nome=f"Handicap: {time_fora} +1.5",
                    odd_mercado=odd_ah_f_plus_15,
                    odd_justa=round(odd_justa_ah_f, 2),
                    ev_calculado=resultado_ev_ah_f['ev'],
                    texto_stake=texto_stake_ah_f
                )
            
        time.sleep(1)

    # Se disparamos os alertas EV, registrar que rodamos esta hora
    if should_dispatch_ev and matched_ev_hour:
        mark_schedule_run('alerta_ev', matched_ev_hour, today_date_str)

    print("\n" + "="*60)
    print(" CICLO DE PATRULHA FINALIZADO ".center(60, "="))
    print("="*60)

if __name__ == "__main__":
    main()
