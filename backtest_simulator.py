import pandas as pd
import requests
import io
import json
import math
import os
from collections import defaultdict

# Configurações do Backtest
INITIAL_BANKROLL = 1000
MIN_EV_THRESHOLD = 0.05  # Aposta apenas se o Valor Esperado for > 5%
CSV_URL = "https://www.football-data.co.uk/mmz4281/2324/E0.csv" # Premier League 23/24
JSON_OUTPUT_PATH = "frontend/public/backtest_results.json"

def get_poisson_probability(lam, k):
    return (math.exp(-lam) * (lam ** k)) / math.factorial(k)

def calculate_kelly_fraction(prob_vitoria, odd_decimal):
    """ Critério de Kelly """
    q = 1 - prob_vitoria
    b = odd_decimal - 1
    if b <= 0: return 0
    f = (b * prob_vitoria - q) / b
    return max(0, f)

def run_backtest():
    print("[!] Iniciando Download da Base de Dados da Premier League 23/24...")
    response = requests.get(CSV_URL)
    df = pd.read_csv(io.StringIO(response.text))
    
    # Limpeza básica
    df = df.dropna(subset=['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'B365H'])
    
    # Estruturas para rastrear gols usando janela deslizante (últimos 5 jogos)
    team_stats = defaultdict(lambda: {
        'scored_home': [], 'conceded_home': [],
        'scored_away': [], 'conceded_away': []
    })
    
    bankroll = INITIAL_BANKROLL
    history = []
    
    total_bets = 0
    won_bets = 0
    
    print("[!] Rodando Motor de Poisson no túnel do tempo...")
    
    # Vamos processar jogo a jogo, na ordem cronológica
    for index, row in df.iterrows():
        home = row['HomeTeam']
        away = row['AwayTeam']
        
        home_goals = int(row['FTHG'])
        away_goals = int(row['FTAG'])
        odd_home_b365 = float(row['B365H'])
        
        # Só apostamos se já tivermos pelo menos 5 jogos de histórico para cada time (para a média ser confiável)
        stats_h = team_stats[home]
        stats_a = team_stats[away]
        
        if len(stats_h['scored_home']) >= 5 and len(stats_a['scored_away']) >= 5:
            # Média de Gols da Janela Deslizante (Últimos 5 Jogos em casa/fora)
            avg_home_scored = sum(stats_h['scored_home'][-5:]) / 5.0
            avg_away_conceded = sum(stats_a['conceded_away'][-5:]) / 5.0
            
            # Cálculo do Lambda (Força de Ataque x Força de Defesa)
            lambda_home = avg_home_scored * avg_away_conceded
            if lambda_home == 0: lambda_home = 0.1
            
            avg_away_scored = sum(stats_a['scored_away'][-5:]) / 5.0
            avg_home_conceded = sum(stats_h['conceded_home'][-5:]) / 5.0
            
            lambda_away = avg_away_scored * avg_home_conceded
            if lambda_away == 0: lambda_away = 0.1
            
            # Probabilidade do Time da Casa vencer (Soma de Placar onde H > A)
            prob_home_win = 0
            for h in range(6):
                for a in range(6):
                    if h > a:
                        p_h = get_poisson_probability(lambda_home, h)
                        p_a = get_poisson_probability(lambda_away, a)
                        prob_home_win += (p_h * p_a)
            
            # Se a probabilidade for > 0, calculamos o EV
            if prob_home_win > 0:
                odd_justa = 1 / prob_home_win
                ev = (prob_home_win * odd_home_b365) - 1
                
                # Se o EV for positivo e bater a nossa meta, APOSTAMOS!
                if ev > MIN_EV_THRESHOLD:
                    kelly = calculate_kelly_fraction(prob_home_win, odd_home_b365)
                    # Limitamos Kelly a 5% max para não quebrar a banca com a volatilidade
                    stake_pct = min(kelly * 0.5, 0.05) 
                    stake = bankroll * stake_pct
                    
                    total_bets += 1
                    
                    if home_goals > away_goals:
                        # Ganhamos a aposta!
                        profit = stake * (odd_home_b365 - 1)
                        bankroll += profit
                        won_bets += 1
                    else:
                        # Perdemos a aposta
                        bankroll -= stake
                        
                    # Registra na curva
                    history.append({
                        "date": row['Date'],
                        "match": f"{home} x {away}",
                        "bankroll": round(bankroll, 2)
                    })
        
        # Atualiza o conhecimento do algoritmo APÓS o jogo (ele aprende no tempo)
        team_stats[home]['scored_home'].append(home_goals)
        team_stats[home]['conceded_home'].append(away_goals)
        
        team_stats[away]['scored_away'].append(away_goals)
        team_stats[away]['conceded_away'].append(home_goals)

    roi = ((bankroll - INITIAL_BANKROLL) / INITIAL_BANKROLL) * 100
    hit_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
    
    print(f"\\n========= RESULTADO DO BACKTEST =========")
    print(f"Banca Inicial: R$ {INITIAL_BANKROLL}")
    print(f"Banca Final: R$ {bankroll:.2f}")
    print(f"Lucro / Prejuízo: {roi:.2f}% (ROI)")
    print(f"Total de Apostas +EV: {total_bets}")
    print(f"Taxa de Acerto: {hit_rate:.2f}%")
    
    # Salvar JSON para o Next.js
    output_data = {
        "stats": {
            "initialBankroll": INITIAL_BANKROLL,
            "finalBankroll": round(bankroll, 2),
            "roi": round(roi, 2),
            "totalBets": total_bets,
            "hitRate": round(hit_rate, 2)
        },
        "chartData": history
    }
    
    os.makedirs(os.path.dirname(JSON_OUTPUT_PATH), exist_ok=True)
    with open(JSON_OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f)
        
    print(f"\\n[!] Arquivo {JSON_OUTPUT_PATH} gerado com sucesso para o Dashboard!")

if __name__ == "__main__":
    run_backtest()
