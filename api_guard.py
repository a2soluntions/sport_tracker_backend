"""
api_guard.py — Proteção contra consumo excessivo da API-Sports.

Camadas de proteção:
1. Lê x-ratelimit-requests-remaining de cada resposta e para se < LIMITE_MINIMO
2. Circuit Breaker: bloqueia chamadas se exceder MAX_REQ_POR_HORA na última hora
3. Registra cada chamada no Supabase (tabela api_usage_log)
4. Alerta no Telegram quando o saldo está baixo
"""

import os
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# ─── Carregar variáveis de ambiente ───────────────────────────────────────────
env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

# ─── Configurações do Guard ───────────────────────────────────────────────────
API_KEY          = os.getenv("API_FOOTBALL_KEY")
API_HOST         = "https://v3.football.api-sports.io"
SUPABASE_URL     = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY     = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Chat do admin (você)

# Limites de segurança
LIMITE_SALDO_MINIMO  = 50    # Para tudo se restar menos de 50 req no dia
LIMITE_AVISO_SALDO   = 200   # Envia alerta no Telegram se restar menos de 200 req
MAX_REQ_POR_HORA     = 80    # Circuit breaker: máx 80 req/hora neste processo
MAX_REQ_POR_DIA_LOG  = 1000  # Aviso de log se ultrapassar 1000 req acumuladas no dia

# Estado em memória do circuit breaker (por processo)
_chamadas_recentes = []       # lista de timestamps das chamadas
_alerta_enviado_hoje = False  # evita spam de alertas
_circuit_aberto = False       # True = circuit breaker ativado, bloqueia chamadas

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _supabase_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

def _registrar_chamada_supabase(endpoint: str, restantes: int, bloqueada: bool = False):
    """Registra a chamada na tabela api_usage_log do Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return
    try:
        payload = {
            "endpoint": endpoint,
            "remaining_quota": restantes,
            "blocked": bloqueada,
            "called_at": datetime.now(timezone.utc).isoformat()
        }
        requests.post(
            f"{SUPABASE_URL}/rest/v1/api_usage_log",
            headers=_supabase_headers(),
            json=payload,
            timeout=5
        )
    except Exception:
        pass  # Não deixa o log quebrar o fluxo principal

def _buscar_total_hoje_supabase() -> int:
    """Retorna quantas chamadas foram feitas hoje (horário UTC)."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return 0
    try:
        hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/api_usage_log?called_at=gte.{hoje}T00:00:00Z&blocked=eq.false&select=id",
            headers=_supabase_headers(),
            timeout=5
        )
        if resp.status_code == 200:
            return len(resp.json())
    except Exception:
        pass
    return 0

def _enviar_alerta_telegram(mensagem: str):
    """Envia alerta para o chat do admin no Telegram."""
    global _alerta_enviado_hoje
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID or _alerta_enviado_hoje:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "HTML"
        }, timeout=5)
        _alerta_enviado_hoje = True
        print(f"[Guard] Alerta enviado no Telegram.")
    except Exception as e:
        print(f"[Guard] Falha ao enviar alerta: {e}")

def _circuit_breaker_ok() -> bool:
    """
    Verifica se o circuit breaker permite uma nova chamada.
    Janela deslizante de 1 hora com MAX_REQ_POR_HORA chamadas.
    """
    global _circuit_aberto, _chamadas_recentes
    agora = time.time()
    # Remove chamadas com mais de 1 hora
    _chamadas_recentes = [t for t in _chamadas_recentes if agora - t < 3600]

    if len(_chamadas_recentes) >= MAX_REQ_POR_HORA:
        if not _circuit_aberto:
            _circuit_aberto = True
            print(f"\033[31m[Guard] CIRCUIT BREAKER ATIVADO! {len(_chamadas_recentes)} req na ultima hora (limite: {MAX_REQ_POR_HORA}).\033[0m")
            _enviar_alerta_telegram(
                f"⚠️ <b>Circuit Breaker Ativado!</b>\n"
                f"O sistema fez <b>{len(_chamadas_recentes)} requisições</b> na última hora.\n"
                f"Limite configurado: <b>{MAX_REQ_POR_HORA}/hora</b>.\n"
                f"Novas chamadas estão bloqueadas até a janela liberar."
            )
        return False

    _circuit_aberto = False
    return True

# ─── Função principal de chamada protegida ───────────────────────────────────

def api_get(endpoint: str, params: dict = None, timeout: int = 15) -> dict | None:
    """
    Substituto seguro para requests.get() nas chamadas à API-Sports.

    Verifica o circuit breaker, faz a chamada, lê o saldo restante,
    registra no log e bloqueia automaticamente se o saldo for crítico.

    Retorna o .json() da resposta ou None se bloqueado/erro.
    """
    global _alerta_enviado_hoje

    if not API_KEY:
        print("\033[31m[Guard] API_FOOTBALL_KEY não configurado. Chamada bloqueada.\033[0m")
        return None

    # 1. Circuit breaker por hora
    if not _circuit_breaker_ok():
        _registrar_chamada_supabase(endpoint, -1, bloqueada=True)
        return None

    url = f"{API_HOST}/{endpoint.lstrip('/')}"
    headers = {"x-apisports-key": API_KEY}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
    except Exception as e:
        print(f"\033[31m[Guard] Erro de rede em {endpoint}: {e}\033[0m")
        return None

    # 2. Ler saldo restante do cabeçalho da resposta
    try:
        restantes = int(resp.headers.get("x-ratelimit-requests-remaining", -1))
    except (ValueError, TypeError):
        restantes = -1

    # 3. Registrar a chamada no Supabase
    _chamadas_recentes.append(time.time())
    _registrar_chamada_supabase(endpoint, restantes)

    # 4. Alerta se saldo está baixo
    if 0 <= restantes <= LIMITE_AVISO_SALDO and not _alerta_enviado_hoje:
        total_hoje = _buscar_total_hoje_supabase()
        _enviar_alerta_telegram(
            f"⚠️ <b>Saldo de API-Sports Baixo!</b>\n"
            f"Restam apenas <b>{restantes} requisições</b> no plano de hoje.\n"
            f"Total consumido hoje (log): <b>{total_hoje} req</b>.\n"
            f"Endpoint atual: <code>{endpoint}</code>\n"
            f"Verifique o painel em: https://dashboard.api-sports.io"
        )

    # 5. Bloquear se saldo crítico
    if 0 <= restantes < LIMITE_SALDO_MINIMO:
        print(f"\033[31m[Guard] BLOQUEIO CRITICO! Apenas {restantes} req restantes. Chamada a '{endpoint}' cancelada.\033[0m")
        return None

    if resp.status_code != 200:
        print(f"\033[33m[Guard] HTTP {resp.status_code} em {endpoint}\033[0m")
        return None

    print(f"[Guard] {endpoint} -> OK | Restantes: {restantes if restantes >= 0 else 'N/A'} | Hora: {len(_chamadas_recentes)}/{MAX_REQ_POR_HORA}")
    return resp.json()


def status_guard() -> dict:
    """Retorna o status atual do guard (para monitoramento)."""
    agora = time.time()
    recentes = [t for t in _chamadas_recentes if agora - t < 3600]
    return {
        "circuit_aberto": _circuit_aberto,
        "req_ultima_hora": len(recentes),
        "limite_hora": MAX_REQ_POR_HORA,
        "alerta_enviado": _alerta_enviado_hoje,
        "total_hoje_estimado": _buscar_total_hoje_supabase()
    }
