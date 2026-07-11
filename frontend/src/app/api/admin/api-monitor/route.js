import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import { verifyAdmin } from '@/lib/adminAuth';

export const dynamic = 'force-dynamic';
export const revalidate = 0;


const API_KEY = process.env.API_FOOTBALL_KEY;
const API_HOST = 'https://v3.football.api-sports.io';
const DEFAULT_BUDGET = 500;

function getSupabaseAdmin() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.SUPABASE_SERVICE_ROLE_KEY,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );
}

// Busca o status real da conta diretamente na API-Sports (/status)
async function fetchApiSportsStatus() {
  if (!API_KEY) return null;
  try {
    const res = await fetch(`${API_HOST}/status`, {
      headers: { 'x-apisports-key': API_KEY },
      cache: 'no-store'
    });
    if (!res.ok) return null;
    const data = await res.json();
    const acc = data?.response?.account;
    const req = data?.response?.requests;
    if (!acc || !req) return null;
    return {
      plano: acc.plan || 'Desconhecido',
      email: acc.email || '',
      reqHoje: req.current ?? -1,
      reqLimite: req.limit_day ?? -1,
      reqRestantes: req.limit_day != null && req.current != null
        ? req.limit_day - req.current
        : -1
    };
  } catch (err) {
    console.warn('[API Monitor] Falha ao buscar /status da API-Sports:', err.message);
    return null;
  }
}

// GET — retorna status atual de uso da API
export async function GET(request) {
  if (!await verifyAdmin(request)) {
    return NextResponse.json({ error: 'Não autorizado' }, { status: 401 });
  }

  const sb = getSupabaseAdmin();
  
  // Define o hoje considerando o fuso horário de Brasília (America/Sao_Paulo)
  const formatter = new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
  const parts = formatter.formatToParts(new Date());
  const day = parts.find(p => p.type === 'day').value;
  const month = parts.find(p => p.type === 'month').value;
  const year = parts.find(p => p.type === 'year').value;
  const hoje = `${year}-${month}-${day}`;


  // Busca todos os dados em paralelo para ser mais rápido
  const [logResult, configResults, apiSportsStatus] = await Promise.allSettled([
    sb
      .from('api_usage_log')
      .select('id, endpoint, remaining_quota, blocked, called_at')
      .gte('called_at', `${hoje}T00:00:00Z`)
      .order('called_at', { ascending: false }),
    sb
      .from('saas_settings')
      .select('key, value')
      .in('key', ['api_sports_blocked', 'api_daily_budget']),
    fetchApiSportsStatus()
  ]);

  // Processa log de uso interno
  const rows = (logResult.status === 'fulfilled' ? logResult.value?.data : null) || [];
  const realizadas = rows.filter(r => !r.blocked).length;
  const bloqueadas = rows.filter(r => r.blocked).length;
  const saldoLogInterno = rows.find(r => r.remaining_quota >= 0)?.remaining_quota ?? -1;

  // Consumo por hora
  const porHora = {};
  rows.forEach(r => {
    const hora = new Date(r.called_at).toLocaleTimeString('pt-BR', {
      timeZone: 'America/Sao_Paulo', hour: '2-digit', hour12: false
    }) + 'h';
    if (!porHora[hora]) porHora[hora] = { realizadas: 0, bloqueadas: 0 };
    if (r.blocked) porHora[hora].bloqueadas++;
    else porHora[hora].realizadas++;
  });

  // Processa configurações do Supabase
  const configRows = (configResults.status === 'fulfilled' ? configResults.value?.data : null) || [];
  const cfgBlocked = configRows.find(c => c.key === 'api_sports_blocked');
  const cfgBudget = configRows.find(c => c.key === 'api_daily_budget');
  const apiBlockedManually = cfgBlocked?.value === true || cfgBlocked?.value === 'true';
  const budgetLimit = cfgBudget?.value ? Number(cfgBudget.value) : DEFAULT_BUDGET;

  // Status direto da API-Sports
  const apiSportsInfo = apiSportsStatus.status === 'fulfilled' ? apiSportsStatus.value : null;

  // Saldo mais preciso: preferir dado direto da API-Sports
  const saldoAtual = apiSportsInfo?.reqRestantes ?? saldoLogInterno;

  // Últimas 30 chamadas para log
  const ultimasChamadas = rows.slice(0, 30).map(r => ({
    id: r.id,
    endpoint: r.endpoint,
    remaining: r.remaining_quota,
    blocked: r.blocked,
    hora: new Date(r.called_at).toLocaleTimeString('pt-BR', {
      timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit'
    })
  }));

  return NextResponse.json({
    hoje: { realizadas, bloqueadas, saldoAtual, data: hoje },
    porHora,
    ultimasChamadas,
    apiBlockedManually,
    budgetLimit,
    apiSportsInfo   // dados diretos da conta: plano, email, req hoje/limite/restantes
  });
}

// POST — controla bloqueio, orçamento e cache
export async function POST(request) {
  if (!await verifyAdmin(request)) {
    return NextResponse.json({ error: 'Não autorizado' }, { status: 401 });
  }

  const body = await request.json();
  const { action, value } = body;

  if (!['block', 'unblock', 'clear_cache', 'set_budget'].includes(action)) {
    return NextResponse.json({ error: 'Ação inválida' }, { status: 400 });
  }

  const sb = getSupabaseAdmin();

  try {
    if (action === 'block' || action === 'unblock') {
      await sb.from('saas_settings').upsert({
        key: 'api_sports_blocked',
        value: action === 'block',
        updated_at: new Date().toISOString()
      }, { onConflict: 'key' });

      return NextResponse.json({
        success: true,
        message: action === 'block'
          ? 'API-Sports bloqueada manualmente. Cache será servido para todos os usuários.'
          : 'API-Sports desbloqueada. Chamadas voltarão ao normal.'
      });
    }

    if (action === 'set_budget') {
      const budget = parseInt(value, 10);
      if (isNaN(budget) || budget < 10 || budget > 100000) {
        return NextResponse.json({ error: 'Valor de orçamento inválido (mínimo 10, máximo 100.000).' }, { status: 400 });
      }
      await sb.from('saas_settings').upsert({
        key: 'api_daily_budget',
        value: budget,
        updated_at: new Date().toISOString()
      }, { onConflict: 'key' });

      return NextResponse.json({
        success: true,
        message: `Orçamento diário atualizado para ${budget} requisições/dia.`
      });
    }

    if (action === 'clear_cache') {
      const { error } = await sb.from('api_cache').delete().neq('cache_key', '__keep__');
      if (error) throw error;
      return NextResponse.json({
        success: true,
        message: 'Cache da API limpo com sucesso. Próximas requisições buscarão dados frescos da API-Sports.'
      });
    }
  } catch (err) {
    console.error('[API Monitor Action] Erro:', err);
    return NextResponse.json({ error: `Erro ao executar ação: ${err.message}` }, { status: 500 });
  }
}
