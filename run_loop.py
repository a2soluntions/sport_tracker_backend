import time
import sys
import os
import traceback

print("============================================================")
print("   INICIANDO MOTOR BACKEND EM LOOP (SCRAPER + POISSON)")
print("============================================================")

def run_orchestrator():
    import main
    main.main()

while True:
    try:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Iniciando ciclo de varredura e resolucao...")
        run_orchestrator()
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [SUCCESS] Ciclo concluído com sucesso.")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [ERROR] Erro durante a execucao: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [WAIT] Aguardando 5 minutos (300 segundos)...")
    time.sleep(300)
