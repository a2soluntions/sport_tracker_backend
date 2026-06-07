def calcular_criterio_kelly(odd_casa: float, probabilidade_real_pct: float, fracao_kelly: float = 0.5) -> dict:
    """
    Calcula a porcentagem ideal da banca (stake) para investir em uma aposta,
    utilizando a fórmula do Critério de Kelly.
    
    Args:
        odd_casa (float): Odd decimal oferecida pela casa de apostas.
        probabilidade_real_pct (float): A probabilidade de vitória gerada pelo seu modelo (em %).
        fracao_kelly (float): Fator de segurança (Kelly Fracionado). Padrão é 0.5 (Half-Kelly).
        
    Returns:
        dict: Dados sobre o tamanho da aposta.
    """
    p = probabilidade_real_pct / 100.0   # Probabilidade de ganhar
    q = 1.0 - p                          # Probabilidade de perder
    b = odd_casa - 1.0                   # Lucro líquido potencial por unidade apostada
    
    # FÓRMULA MATEMÁTICA DE KELLY: f* = (bp - q) / b
    f_star = (b * p - q) / b
    
    # Se f_star for menor ou igual a 0, significa que não há margem de lucro matemático (-EV).
    # O Critério de Kelly matematicamente proíbe apostas sem valor.
    if f_star <= 0:
        return {
            "tem_valor": False,
            "porcentagem_banca_full": 0.0,
            "porcentagem_banca_ajustada": 0.0,
            "recomendacao": "NÃO APOSTAR (-EV ou Edge Nulo)"
        }
        
    # KELLY FRACIONADO (Segurança Institucional)
    # O Kelly "Full" (1.0) maximiza o lucro matemático no longo prazo, mas causa uma
    # volatilidade extrema na banca (drawdowns psicológicos muito severos).
    # O mercado profissional adota Kelly Fracionado (geralmente entre 0.25 e 0.50)
    # para crescer a banca com segurança e suportar as famosas "Bad Runs" (sequência de perdas).
    f_ajustado = f_star * fracao_kelly
    
    return {
        "tem_valor": True,
        "porcentagem_banca_full": f_star * 100,
        "porcentagem_banca_ajustada": f_ajustado * 100,
        "recomendacao": f"Investir {f_ajustado * 100:.2f}% do Capital."
    }

if __name__ == "__main__":
    # --- SIMULAÇÃO PRÁTICA ---
    # Vamos usar o alerta do Módulo 3.
    # Nosso motor Poisson achou uma Odd Justa de 1.82 (55% de probabilidade real de vitória).
    # O robô de Scraping viu que a Casa de Apostas "dormiu no ponto" e está pagando odd de 2.10.
    
    odd_do_mercado = 2.10
    probabilidade_do_nosso_modelo = 55.0
    
    # Capital de giro do investidor (Banca)
    banca_disponivel = 1000.00
    
    print(f"\033[38;2;204;255;0m--- GESTÃO DE RISCO MATEMÁTICA (CRITÉRIO DE KELLY) ---\033[0m")
    print(f"Cenário Encontrado: ODD {odd_do_mercado} | Sua Chance Real: {probabilidade_do_nosso_modelo}%")
    
    # Calculando usando Half-Kelly (Fator 0.5 de proteção)
    gestao = calcular_criterio_kelly(odd_do_mercado, probabilidade_do_nosso_modelo, fracao_kelly=0.5)
    
    if gestao['tem_valor']:
        print("\n[>] Diagnóstico do Algoritmo:")
        print(f"Kelly Completo (Agressivo máximo): {gestao['porcentagem_banca_full']:.2f}% da banca.")
        print(f"Half-Kelly (Modo Profissional): {gestao['porcentagem_banca_ajustada']:.2f}% da banca.")
        
        valor_financeiro = banca_disponivel * (gestao['porcentagem_banca_ajustada'] / 100.0)
        
        print(f"\n[!] AÇÃO DE EXECUÇÃO:")
        print(f"Com uma banca de R$ {banca_disponivel:.2f}, sua 'Stake' ideal será de exatos: R$ {valor_financeiro:.2f}")
    else:
        print(f"\n[!] ALERTA VERMELHO: {gestao['recomendacao']}")
