from database_connector import banco_de_dados

try:
    for status in ['pending', 'green', 'red', 'expired', 'void']:
        resp = banco_de_dados.table('ev_opportunities').select('id', count='exact').eq('resultado', status).execute()
        print(f"Status '{status}': {resp.count}")
except Exception as e:
    print("Error:", e)
