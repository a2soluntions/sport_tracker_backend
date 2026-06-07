import numpy as np
from scipy.stats import poisson

def calcular_probabilidades_poisson(xg_casa: float, xg_fora: float, tempo_decorrido: int = 0, gols_casa_atuais: int = 0, gols_fora_atuais: int = 0) -> dict:
    """
    Motor Estatístico Bidimensional + Módulo Ao Vivo (Time-Decay).
    Calcula Vencedor da Partida e Total de Gols, descontando o tempo que já passou.
    """
    # 1. TIME-DECAY: Quanto do jogo ainda resta?
    tempo_restante = max(0, 90 - tempo_decorrido)
    fator_tempo = tempo_restante / 90.0
    
    # xG para o resto do jogo
    xg_casa_restante = max(0.001, xg_casa * fator_tempo)
    xg_fora_restante = max(0.001, xg_fora * fator_tempo)
    
    max_gols_restantes = 10
    matriz_probabilidades = np.zeros((max_gols_restantes, max_gols_restantes))
    
    # 2. PREENCHENDO A MATRIZ DE PLACARES PARA O RESTO DO JOGO
    for gols_casa_r in range(max_gols_restantes):
        for gols_fora_r in range(max_gols_restantes):
            prob_casa_marcar = poisson.pmf(gols_casa_r, xg_casa_restante)
            prob_fora_marcar = poisson.pmf(gols_fora_r, xg_fora_restante)
            matriz_probabilidades[gols_casa_r, gols_fora_r] = prob_casa_marcar * prob_fora_marcar
            
    # 3. CONVERTER PARA O PLACAR FINAL (Somando com o que já aconteceu)
    prob_vitoria_casa = 0
    prob_empate = 0
    prob_vitoria_fora = 0
    
    prob_under_25 = 0
    prob_over_25 = 0
    
    for gols_casa_r in range(max_gols_restantes):
        for gols_fora_r in range(max_gols_restantes):
            probabilidade = matriz_probabilidades[gols_casa_r, gols_fora_r]
            
            placar_final_casa = gols_casa_atuais + gols_casa_r
            placar_final_fora = gols_fora_atuais + gols_fora_r
            
            # Match Odds (1X2)
            if placar_final_casa > placar_final_fora:
                prob_vitoria_casa += probabilidade
            elif placar_final_casa == placar_final_fora:
                prob_empate += probabilidade
            else:
                prob_vitoria_fora += probabilidade
                
            # Over/Under 2.5 Gols
            total_gols_final = placar_final_casa + placar_final_fora
            if total_gols_final <= 2:
                prob_under_25 += probabilidade
            else:
                prob_over_25 += probabilidade
    
    # 4. NORMALIZAÇÃO (Garantir 100%)
    total_1x2 = prob_vitoria_casa + prob_empate + prob_vitoria_fora
    total_gols = prob_under_25 + prob_over_25
    
    p_casa_pct = (prob_vitoria_casa / total_1x2) * 100
    p_empate_pct = (prob_empate / total_1x2) * 100
    p_fora_pct = (prob_vitoria_fora / total_1x2) * 100
    
    p_under_25_pct = (prob_under_25 / total_gols) * 100
    p_over_25_pct = (prob_over_25 / total_gols) * 100
    
    return {
        "prob_casa_pct": p_casa_pct,
        "prob_empate_pct": p_empate_pct,
        "prob_fora_pct": p_fora_pct,
        "odd_justa_casa": 100 / max(0.01, p_casa_pct),
        "odd_justa_empate": 100 / max(0.01, p_empate_pct),
        "odd_justa_fora": 100 / max(0.01, p_fora_pct),
        
        "prob_under_25_pct": p_under_25_pct,
        "prob_over_25_pct": p_over_25_pct,
        "odd_justa_under_25": 100 / max(0.01, p_under_25_pct),
        "odd_justa_over_25": 100 / max(0.01, p_over_25_pct)
    }

if __name__ == "__main__":
    print("[>] Testando Motor: Jogo empatado 1x1 aos 75 minutos")
    resultados = calcular_probabilidades_poisson(1.85, 1.10, tempo_decorrido=75, gols_casa_atuais=1, gols_fora_atuais=1)
    print(f"Fair Line Casa (para desempatar e vencer nos ultimos 15 min): {resultados['odd_justa_casa']:.2f}")
    print(f"Fair Line Over 2.5 (1 gol a mais p/ bater over 2.5): {resultados['odd_justa_over_25']:.2f}")
    print(f"Fair Line Under 2.5 (Jogo terminar 1x1): {resultados['odd_justa_under_25']:.2f}")
