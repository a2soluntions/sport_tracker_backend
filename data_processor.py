import pandas as pd

def processar_historico_jogos(caminho_csv: str = None) -> pd.DataFrame:
    """
    Carrega o histórico de partidas (planilha, CSV ou banco de dados), 
    faz a limpeza (Data Cleaning) e prepara o DataFrame estruturado.
    """
    # 1. CARREGAMENTO
    # Na vida real, você puxaria de uma API ou de planilhas famosas gratuitas como as do 'Football-Data.co.uk':
    # df = pd.read_csv('england_premier_league.csv')
    
    # Para o nosso laboratório, vamos criar um DataFrame fictício (Mock) simulando a base:
    dados_mock = [
        {"data": "2026-04-10", "time_casa": "Arsenal", "time_fora": "Chelsea", "gols_casa": 2, "gols_fora": 0},
        {"data": "2026-04-17", "time_casa": "Liverpool", "time_fora": "Arsenal", "gols_casa": 1, "gols_fora": 1},
        {"data": "2026-04-24", "time_casa": "Arsenal", "time_fora": "Newcastle", "gols_casa": 3, "gols_fora": 1},
        {"data": "2026-04-11", "time_casa": "Atlético Madrid", "time_fora": "Sevilla", "gols_casa": 1, "gols_fora": 0},
        {"data": "2026-04-18", "time_casa": "Real Madrid", "time_fora": "Atlético Madrid", "gols_casa": 2, "gols_fora": 1},
        {"data": "2026-04-25", "time_casa": "Atlético Madrid", "time_fora": "Valencia", "gols_casa": 1, "gols_fora": 0},
    ]
    df = pd.DataFrame(dados_mock)
    
    # 2. LIMPEZA DE DADOS (Data Cleaning)
    # Se alguma linha vier sem o número de gols, nós a descartamos para não bugar o modelo.
    df.dropna(subset=['gols_casa', 'gols_fora'], inplace=True)
    
    # Padronizar datas (para filtrar por temporada ou forma recente)
    df['data'] = pd.to_datetime(df['data'])
    
    # 3. ENGENHARIA DE RECURSOS (Feature Engineering)
    # Podemos criar colunas que não existiam, ex: total_de_gols_na_partida
    df['total_gols'] = df['gols_casa'] + df['gols_fora']
    
    return df

def calcular_xg_basico(df: pd.DataFrame, time_analisado: str, jogar_em: str = 'casa') -> float:
    """
    Uma versão educacional e simplificada para calcular a expectativa de gols (xG) 
    baseada na média móvel do time.
    Em um modelo avançado, incluiríamos a "Força da Defesa" do adversário aqui.
    """
    if jogar_em == 'casa':
        # Filtra na base Pandas: Apenas as linhas onde 'time_casa' é o nosso time
        jogos = df[df['time_casa'] == time_analisado]
        if jogos.empty: 
            return 1.0 # Valor default de segurança se o time for novato na liga
            
        # O Pandas tira a média com um único comando (.mean())
        media_marcados = jogos['gols_casa'].mean()
        return media_marcados
        
    elif jogar_em == 'fora':
        # Filtra: Apenas as linhas onde 'time_fora' é o nosso time
        jogos = df[df['time_fora'] == time_analisado]
        if jogos.empty: 
            return 1.0
            
        media_marcados = jogos['gols_fora'].mean()
        return media_marcados
        
    return 1.0

if __name__ == "__main__":
    print(f"\033[38;2;204;255;0m--- MÓDULO PANDAS (PROCESSAMENTO DE DADOS) ---\033[0m")
    
    # Passo A: Processar e Estruturar o Banco Bruto
    print("[-] Carregando e limpando o histórico de confrontos...")
    tabela_limpa = processar_historico_jogos()
    
    print("\nVisualização do Pandas DataFrame:")
    print(tabela_limpa)
    
    # Passo B: Extrair Inteligência (Mineração)
    # O jogo de hoje é Arsenal (Casa) contra Atlético de Madrid (Fora).
    
    xg_home_arsenal = calcular_xg_basico(tabela_limpa, "Arsenal", jogar_em='casa')
    xg_away_atletico = calcular_xg_basico(tabela_limpa, "Atlético Madrid", jogar_em='fora')
    
    print("\n[>] Inteligência Extraída e Preparada para o Modelo Poisson:")
    print(f"-> Força do Arsenal em Casa (xG): {xg_home_arsenal:.2f} gols por jogo.")
    print(f"-> Força do Atlético Fora (xG): {xg_away_atletico:.2f} gols por jogo.")
    
    print("\n[!] O CICLO SE CONECTA AQUI:")
    print(f"Você pega esses valores (Arsenal: {xg_home_arsenal}, Atlético: {xg_away_atletico})")
    print("e injeta diretamente no 'poisson_model.py'!")
