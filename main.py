import time
import random
from scraper import coletar_odds_betano
from live_scraper import coletar_odds_ao_vivo
from poisson_model import calcular_probabilidades_poisson
from ev_calculator import calcular_ev
from database_connector import gravar_oportunidade_ev, ler_configuracoes_usuario
from kelly_criterion import calcular_criterio_kelly
from alert_dispatcher import despachar_alertas_personalizados
import result_resolver

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
    banca_usuario, ligas_alvo = ler_configuracoes_usuario()
    print(f"[-] Configuração Ativa: Banca de R$ {banca_usuario:.2f} | Alvos: {len(ligas_alvo)} Ligas")

    if not ligas_alvo:
        print("\n\033[31m[X] Nenhuma liga selecionada no painel. Abortando ciclo.\033[0m")
        return

    # 2. Crawler Múltiplas Ligas (Pré-Jogo e Ao Vivo)
    jogos_pre_match = coletar_odds_betano(ligas_alvo)
    jogos_ao_vivo = coletar_odds_ao_vivo(["https://br.betano.com/live/"])
    
    jogos_raspados = jogos_pre_match + jogos_ao_vivo
    
    if not jogos_raspados:
        print("\n\033[31m[X] Nenhum jogo processado na varredura. Abortando ciclo.\033[0m")
        return

    print("\n\033[36m[!] Iniciando Motor de Poisson Bidimensional...\033[0m")
    
    # 3. Processa os jogos coletados
    for jogo in jogos_raspados:
        print(f"\n\033[1mAnalisando: {jogo['confronto']} ({jogo['campeonato']})\033[0m")
        
        xg_casa_simulado = random.uniform(1.2, 2.8) 
        xg_fora_simulado = random.uniform(0.5, 1.9)
        
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
            
            # Dispara Notificação Celular Personalizada
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
            
            # Dispara Notificação Celular Personalizada
            despachar_alertas_personalizados(
                confronto=jogo['confronto'],
                campeonato=jogo['campeonato'],
                mercado="Mais de 2.5 Gols",
                odd_oferecida=odd_over_mercado,
                odd_justa=round(odd_justa_over, 2),
                ev_decimal=resultado_ev_gols['ev'],
                is_live=jogo.get('is_live', False)
            )
            
        time.sleep(1)

    print("\n" + "="*60)
    print(" CICLO DE PATRULHA FINALIZADO ".center(60, "="))
    print("="*60)

if __name__ == "__main__":
    main()
