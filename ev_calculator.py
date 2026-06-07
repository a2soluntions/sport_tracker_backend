def calcular_ev(odd_casa: float, probabilidade_calculada_pct: float) -> dict:
    """
    Calcula o Valor Esperado (EV) de uma aposta.
    
    Args:
        odd_casa (float): A odd decimal oferecida pela casa de apostas (ex: 2.10).
        probabilidade_calculada_pct (float): A probabilidade de vitória calculada pelo seu modelo, em porcentagem (ex: 55.0).
        
    Returns:
        dict: Um dicionário contendo o EV calculado, o status (se tem valor ou não) e outras métricas.
    """
    # 1. Converter a porcentagem para decimal (ex: 55% -> 0.55)
    p_ganhar = probabilidade_calculada_pct / 100.0
    p_perder = 1.0 - p_ganhar
    
    # 2. Assumindo uma aposta padrão de 1 unidade
    valor_apostado = 1.0
    lucro_potencial = odd_casa - 1.0 # O que você ganha de lucro líquido se vencer
    
    # 3. Fórmula do Valor Esperado (EV)
    # EV = (Probabilidade de Ganhar * Lucro Potencial) - (Probabilidade de Perder * Valor Apostado)
    ev = (p_ganhar * lucro_potencial) - (p_perder * valor_apostado)
    
    # Observação: Uma forma simplificada matematicamente para o mesmo cálculo é: 
    # EV = (p_ganhar * odd_casa) - 1
    
    # 4. Avaliar se a aposta tem valor
    tem_valor = ev > 0
    
    # 5. Formatação visual baseada nas cores de referência (Verde Neon / Vermelho)
    # Utilizando ANSI escape codes para colorir o terminal
    cor_alerta = "\033[38;2;204;255;0m" if tem_valor else "\033[91m" # RGB para Verde Neon (CCFF00) ou Vermelho padrão
    reset_cor = "\033[0m"
    
    recomendacao = "APOSTA COM VALOR (+EV)" if tem_valor else "DESCARTAR (-EV)"
    
    print(f"--- Análise de Oportunidade ---")
    print(f"Odd da Casa: {odd_casa}")
    print(f"Sua Probabilidade Real: {probabilidade_calculada_pct}%")
    print(f"Valor Esperado (EV): {cor_alerta}{ev:+.4f} unidades{reset_cor}")
    print(f"Ação Recomendada: {cor_alerta}{recomendacao}{reset_cor}\n")
    
    return {
        "ev": ev,
        "tem_valor": tem_valor,
        "odd": odd_casa,
        "probabilidade_real": p_ganhar
    }

if __name__ == "__main__":
    # Teste 1: Cenário com Valor Esperado Positivo (+EV)
    # A casa oferece odd 2.10 (probabilidade implícita de 47.6%)
    # Nosso modelo estatístico calculou 55% de chance de vitória.
    print("CENÁRIO 1: Encontrando distorção favorável")
    calcular_ev(odd_casa=2.10, probabilidade_calculada_pct=55.0)
    
    # Teste 2: Cenário sem valor (-EV)
    # A casa oferece odd 1.50 (probabilidade implícita de 66.6%)
    # Nosso modelo calculou apenas 60% de chance de vitória.
    print("CENÁRIO 2: Odd esmagada (sem valor)")
    calcular_ev(odd_casa=1.50, probabilidade_calculada_pct=60.0)
