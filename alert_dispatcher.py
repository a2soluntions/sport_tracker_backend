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
    Despacha alertas personalizados para cada assinante ativo de acordo com suas regras e canais configurados.
    """
    if not supabase:
        print("[Dispatcher] Supabase não inicializado. Realizando broadcast padrão como fallback...")
        # Fallback para broadcast geral se não houver conexão com Supabase
        ev_porcentagem = ev_decimal * 100 if ev_decimal < 1.0 else ev_decimal
        enviar_alerta_telegram(confronto, campeonato, mercado, odd_oferecida, odd_justa, ev_porcentagem, "R$ 50.00 (Fixo)", is_live)
        return

    try:
        # 1. Carregar todos os perfis para saber quem é admin ou pagante
        profiles_resp = supabase.table("profiles").select("id, plan, role, email").execute()
        profiles = {p["id"]: p for p in profiles_resp.data} if profiles_resp.data else {}

        # 2. Carregar configurações de todos os usuários com Telegram ativo
        settings_resp = supabase.table("user_settings").select("*").eq("receive_telegram", True).execute()
        users_settings = settings_resp.data or []

        if not users_settings:
            print("[Dispatcher] Nenhum usuário configurado para receber notificações personalizadas.")
            return

        print(f"[Dispatcher] Analisando envio para {len(users_settings)} usuários ativos...")

        # Converter EV decimal em porcentagem para filtros e visualização
        ev_porcentagem = ev_decimal * 100 if ev_decimal < 1.0 else ev_decimal
        probabilidade_real_pct = 100.0 / odd_justa if odd_justa > 0 else 50.0

        for user_setting in users_settings:
            user_id = user_setting.get("id")
            chat_id = user_setting.get("telegram_chat_id")

            if not chat_id:
                continue

            profile = profiles.get(user_id)
            if not profile:
                continue

            # Regra de plano: apenas admins ou usuários com plano ativo (pro, vip, vitalicio) recebem alertas
            plano = profile.get("plan", "gratis")
            role = profile.get("role", "user")
            
            is_admin = role in ["admin", "super_admin"]
            is_active_subscriber = plano in ["pro", "vip", "vitalicio"]

            if not is_admin and not is_active_subscriber:
                # Usuário gratuito não recebe alertas premium
                continue

            # Filtro de EV Mínimo Pessoal
            min_ev_pessoal = float(user_setting.get("min_ev") or 5.00)
            if ev_porcentagem < min_ev_pessoal:
                print(f"   [-] Pulando {profile['email']}: EV de +{ev_porcentagem:.2f}% é menor que o mínimo de {min_ev_pessoal}%")
                continue

            # Filtro de Alerta Pré-Jogo
            if not is_live and not user_setting.get("alert_prematch", True):
                print(f"   [-] Pulando {profile['email']}: Desativou alertas Pré-Jogo")
                continue

            # Filtro de Alerta Ao Vivo
            if is_live and not user_setting.get("alert_live", True):
                print(f"   [-] Pulando {profile['email']}: Desativou alertas Ao Vivo")
                continue

            # Cálculo de Gestão de Banca Personalizada
            banca_pessoal = float(user_setting.get("banca") or 1000.00)
            stake_info = calcular_criterio_kelly(odd_oferecida, probabilidade_real_pct, 0.25)
            pct_ajustada = stake_info.get("porcentagem_banca_ajustada", 0.0)
            
            valor_stake_pessoal = banca_pessoal * (pct_ajustada / 100.0)
            aposta_sugerida_personalizada = f"R$ {valor_stake_pessoal:.2f} ({pct_ajustada:.1f}%)"

            # Envia o alerta customizado para o Telegram deste usuário
            print(f"   [+] Despachando para {profile['email']} (Chat ID: {chat_id}) | Banca: R$ {banca_pessoal:.2f}")
            enviar_alerta_telegram(
                confronto=confronto,
                campeonato=campeonato,
                mercado=mercado,
                odd_oferecida=odd_oferecida,
                odd_justa=odd_justa,
                ev=ev_porcentagem,
                aposta_sugerida=aposta_sugerida_personalizada,
                is_live=is_live,
                chat_id=chat_id
            )

    except Exception as e:
        print(f"\033[31m[X] Erro ao despachar alertas personalizados: {e}\033[0m")
