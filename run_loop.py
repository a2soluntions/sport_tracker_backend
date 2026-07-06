import time
import sys
import os
import traceback
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

print("============================================================")
print("   INICIANDO MOTOR BACKEND EM LOOP (SCRAPER + POISSON)   ")
print("============================================================")

def ping_auto_dispatch():
    try:
        app_url = os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3000").rstrip("/")
        url_auto = f"{app_url}/api/telegram/auto-dispatch"
        headers = {"Authorization": f"Bearer {os.getenv('SUPABASE_SERVICE_ROLE_KEY')}"}
        resp = requests.post(url_auto, headers=headers, timeout=10)
        if resp.status_code == 200:
            res_json = resp.json()
            palpites_status = res_json.get("palpites", {})
            if palpites_status.get("dispatched"):
                print(f"[{time.strftime('%H:%M:%S')}] [Auto-Broadcast] Palpites disparados com sucesso via API Next.js!")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] [Auto-Broadcast] Status {resp.status_code} ao pingar Next.js")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] [Auto-Broadcast] Erro ao pingar Next.js auto-dispatch: {e}")

last_scraper_run = 0
last_dispatch_ping = 0

# Intervalo do scraper: 2 horas (7200 segundos) para economizar requisições da API-Sports
SCRAPER_INTERVAL = 7200
# Intervalo do ping de auto-dispatch: 1 minuto (60 segundos) para precisão cirúrgica
DISPATCH_PING_INTERVAL = 60

while True:
    current_time = time.time()

    # 1. Ping o auto-dispatch do Next.js a cada 5 minutos (era 30s - desperdício)
    if current_time - last_dispatch_ping >= DISPATCH_PING_INTERVAL:
        ping_auto_dispatch()
        last_dispatch_ping = current_time

    # 2. Executa a varredura completa do scraper a cada 2 HORAS (era 30 min - alto consumo)
    if current_time - last_scraper_run >= SCRAPER_INTERVAL:
        try:
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Iniciando ciclo de varredura completa do Scraper...")
            import main
            import importlib
            importlib.reload(main)
            main.main()
            last_scraper_run = time.time()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [SUCCESS] Ciclo de varredura concluído.")
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] Erro no Scraper: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            # Tenta novamente em 30 minutos se falhar
            last_scraper_run = time.time() - (SCRAPER_INTERVAL - 1800)

    time.sleep(60)
