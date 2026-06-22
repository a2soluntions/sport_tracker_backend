from database_connector import banco_de_dados

def check_db_opps():
    try:
        # Buscar oportunidades pendentes recentes
        resp = banco_de_dados.table('ev_opportunities').select('*').order('created_at', desc=True).limit(50).execute()
        if resp.data:
            print("Últimas 50 oportunidades gravadas no banco:")
            for o in resp.data:
                print(f"[{o['created_at']}] {o['confronto']} ({o['campeonato']}) | Mercado: {o['mercado']} | EV: +{o['vantagem_ev_porcentagem']}%")
        else:
            print("Nenhuma oportunidade gravada no banco.")
    except Exception as e:
        print("Erro ao ler ev_opportunities:", e)

if __name__ == "__main__":
    check_db_opps()
