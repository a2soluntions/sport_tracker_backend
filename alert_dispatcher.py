import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from kelly_criterion import calcular_criterio_kelly
from telegram_bot import enviar_alerta_telegram

# Carregar variáveis de ambiente do frontend/.env.local ou .env local
env_path = os.path.join(os.path.dirname(__file__), "frontend", ".env.local")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("\033[31m[X] Erro: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não configurados para o Dispatcher.\033[0m")
    supabase = None
else:
    supabase: Client = create_client(supabase_url, supabase_key)

def despachar_alertas_personalizados(confronto, campeonato, mercado, odd_oferecida, odd_justa, ev_decimal, is_live=False):
    """
    Despacha alertas +EV diretamente para o Canal/Grupo VIP configurado.
    """
    vip_chat_id = os.getenv("TELEGRAM_VIP_CHAT_ID")
    if not vip_chat_id:
        print("[Dispatcher] Erro: TELEGRAM_VIP_CHAT_ID nao configurado no .env.")
        return

    # Converter EV decimal em porcentagem para visualização
    ev_porcentagem = ev_decimal * 100 if ev_decimal < 1.0 else ev_decimal
    probabilidade_real_pct = 100.0 / odd_justa if odd_justa > 0 else 50.0

    # Filtro padrão de EV Mínimo global para o grupo VIP (ex: 5%)
    min_ev_grupo = 5.0
    if ev_porcentagem < min_ev_grupo:
        print(f"[Dispatcher] Ignorando jogo com EV de +{ev_porcentagem:.2f}% (menor que o minimo de {min_ev_grupo}%)")
        return

    # Cálculo da Stake Sugerida pela gestão de banca (Critério de Kelly)
    # Usando banca teórica ou apenas a porcentagem recomendada
    stake_info = calcular_criterio_kelly(odd_oferecida, probabilidade_real_pct, 0.25)
    pct_ajustada = stake_info.get("porcentagem_banca_ajustada", 0.0)
    aposta_sugerida_personalizada = f"{pct_ajustada:.1f}%"

    print(f"[Dispatcher] Enviando sinal para o Grupo VIP ({vip_chat_id}) | EV: +{ev_porcentagem:.2f}%")
    
    enviar_alerta_telegram(
        confronto=confronto,
        campeonato=campeonato,
        mercado=mercado,
        odd_oferecida=odd_oferecida,
        odd_justa=odd_justa,
        ev=ev_porcentagem,
        aposta_sugerida=aposta_sugerida_personalizada,
        is_live=is_live,
        chat_id=vip_chat_id
    )

