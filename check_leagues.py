from database_connector import banco_de_dados
import requests
import json

def check():
    try:
        resp = banco_de_dados.table('saas_settings').select('*').eq('key', 'target_leagues').execute()
        if resp.data:
            print("Ligas configuradas no banco de dados:")
            print(json.dumps(resp.data[0]['value'], indent=2, ensure_ascii=False))
        else:
            print("Nenhuma liga configurada no saas_settings.")
    except Exception as e:
        print("Erro ao ler saas_settings:", e)

if __name__ == "__main__":
    check()
