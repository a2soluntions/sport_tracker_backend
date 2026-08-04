import { NextResponse } from 'next/server';
import { getCurrentRound, getStandings } from 'campeonato-brasileiro-api';
import { createClient } from '@supabase/supabase-js';
import { logApiCall } from '@/lib/apiLogger';

const API_KEY = process.env.API_FOOTBALL_KEY;
const API_HOST = 'https://v3.football.api-sports.io';

// Cache em memória como camada L1 (válido enquanto a instância serverless viver)
const memCache = { fixtures: {}, stats: {} };
const CACHE_DURATION_MS = 30 * 60 * 1000; // 30 minutos

// ─── Orçamento diário de segurança ────────────────────────────────────────────
// Bloqueia chamadas à API-Sports se exceder este limite no dia (lido dinamicamente do Supabase)
let _budgetCheckedAt = 0;
let _budgetExceeded = false;
let _apiBlockedManually = false;

// Cache persistente no Supabase como camada L2 (sobrevive ao cold start serverless)
function getSupabaseAdmin() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) return null;
  return createClient(url, key, { auth: { autoRefreshToken: false, persistSession: false } });
}

async function getCachedData(cacheKey) {
  const now = Date.now();
  // L1: memória
  if (memCache.fixtures[cacheKey] && (now - memCache.fixtures[cacheKey].timestamp) < CACHE_DURATION_MS) {
    return { data: memCache.fixtures[cacheKey].data, hit: 'memory' };
  }
  // L2: Supabase
  try {
    const sb = getSupabaseAdmin();
    if (!sb) return null;
    const { data } = await sb.from('api_cache').select('payload, cached_at').eq('cache_key', cacheKey).single();
    if (data) {
      const age = now - new Date(data.cached_at).getTime();
      if (age < CACHE_DURATION_MS) {
        memCache.fixtures[cacheKey] = { data: data.payload, timestamp: now - age };
        return { data: data.payload, hit: 'supabase' };
      }
    }
  } catch (_) {}
  return null;
}

async function setCachedData(cacheKey, data) {
  memCache.fixtures[cacheKey] = { data, timestamp: Date.now() };
  try {
    const sb = getSupabaseAdmin();
    if (!sb) return;
    await sb.from('api_cache').upsert({ cache_key: cacheKey, payload: data, cached_at: new Date().toISOString() }, { onConflict: 'cache_key' });
  } catch (_) {}
}

async function fetchAndLog(url, endpointName) {
  const res = await fetch(url, { headers: { 'x-apisports-key': API_KEY } });
  const remaining = Number(res.headers.get('x-ratelimit-requests-remaining') ?? -1);
  logApiCall(endpointName, remaining, false);
  return res;
}

/**
 * Verifica se o orçamento diário de API foi excedido ou se a API foi bloqueada manualmente.
 * Consulta o Supabase (api_usage_log, saas_settings) e faz cache de 1 minuto em memória.
 */
async function isBudgetExceeded() {
  const now = Date.now();
  // Reutiliza verificação por 1 minuto
  if (now - _budgetCheckedAt < 1 * 60 * 1000) return _budgetExceeded || _apiBlockedManually;

  try {
    const sb = getSupabaseAdmin();
    if (!sb) { _budgetCheckedAt = now; return false; }

    const hoje = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
    
    // 1. Busca configurações (limite diário e bloqueio manual)
    const { data: configRows } = await sb
      .from('saas_settings')
      .select('key, value')
      .in('key', ['api_sports_blocked', 'api_daily_budget']);

    const cfgBlocked = configRows?.find(c => c.key === 'api_sports_blocked');
    const cfgBudget = configRows?.find(c => c.key === 'api_daily_budget');
    
    _apiBlockedManually = cfgBlocked?.value === true || cfgBlocked?.value === 'true';
    const limit = cfgBudget?.value ? Number(cfgBudget.value) : 500;

    // 2. Conta chamadas realizadas hoje
    const { count, error } = await sb
      .from('api_usage_log')
      .select('*', { count: 'exact', head: true })
      .gte('called_at', `${hoje}T00:00:00Z`)
      .eq('blocked', false);

    const total = count ?? 0;
    _budgetExceeded = total >= limit;
    _budgetCheckedAt = now;

    if (_apiBlockedManually) {
      console.warn(`[Budget Guard] API-Sports bloqueada manualmente no painel admin.`);
    }
    if (_budgetExceeded) {
      console.warn(`[Budget Guard] Orçamento diário atingido: ${total}/${limit} req. Usando apenas cache.`);
    }
    return _budgetExceeded || _apiBlockedManually;
  } catch (err) {
    console.error('[Budget Guard] Erro na verificação do orçamento:', err);
    _budgetCheckedAt = now;
    return false;
  }
}

// ==========================================
// TABELA DE FORÇA DOS TIMES (xG base)
// Baseado em ranking FIFA / desempenho real
// xG = gols esperados por jogo (~1.0 fraco, 2.5 forte)
// ==========================================
const TEAM_STRENGTH = {
  // Seleções - Top tier (xG ~2.0–2.5)
  'Argentina': 2.3,
  'France': 2.2,
  'England': 2.1,
  'Spain': 2.2,
  'Brazil': 2.1,
  'Portugal': 2.1,
  'Belgium': 1.9,
  'Germany': 2.0,
  'Netherlands': 2.0,
  'Italy': 1.8,
  'Croatia': 1.7,
  'Uruguay': 1.8,
  'Colombia': 1.7,
  'Morocco': 1.6,
  'Switzerland': 1.6,
  'Denmark': 1.6,
  'Austria': 1.5,
  'Mexico': 1.6,
  'USA': 1.5,
  'Japan': 1.6,
  'South Korea': 1.5,
  'Senegal': 1.5,
  'Ecuador': 1.4,
  'Wales': 1.4,
  'Serbia': 1.5,
  'Ukraine': 1.5,
  'Hungary': 1.4,
  'Poland': 1.5,
  'Turkey': 1.5,
  'Czech Republic': 1.4,
  'Romania': 1.3,
  'Slovakia': 1.3,
  'Scotland': 1.4,
  'Australia': 1.4,
  'Iran': 1.3,
  'Saudi Arabia': 1.3,
  'Qatar': 1.2,
  'Tunisia': 1.3,
  'Cameroon': 1.3,
  'Ghana': 1.3,
  'Nigeria': 1.4,
  'Egypt': 1.4,
  'Algeria': 1.3,
  'Ivory Coast': 1.3,
  'Canada': 1.3,
  'Costa Rica': 1.2,
  'Paraguay': 1.3,
  'Chile': 1.4,
  'Peru': 1.3,
  'Bolivia': 1.1,
  'Venezuela': 1.2,
  'Panama': 1.1,
  'Honduras': 1.1,
  'El Salvador': 1.0,
  'Guatemala': 1.0,
  'Jordan': 1.1,
  'Iraq': 1.2,
  'Syria': 1.1,
  'Palestine': 1.0,
  'Oman': 1.0,
  'Bahrain': 1.0,
  'UAE': 1.1,
  'Kuwait': 1.0,
  'New Zealand': 1.1,
  'Jamaica': 1.1,
  'Haiti': 1.0,
  'Cuba': 1.0,
  'Trinidad and Tobago': 1.1,
  'Curacao': 1.0,
  // Clubes - Elite (xG ~1.8–2.5)
  'Manchester City': 2.4,
  'Real Madrid': 2.3,
  'Bayern Munich': 2.3,
  'Liverpool': 2.2,
  'Barcelona': 2.2,
  'Arsenal': 2.0,
  'Chelsea': 1.9,
  'Manchester United': 1.9,
  'Tottenham': 1.8,
  'Atletico Madrid': 1.8,
  'Inter': 1.9,
  'Napoli': 1.8,
  'Juventus': 1.7,
  'AC Milan': 1.7,
  'Borussia Dortmund': 1.9,
  'PSG': 2.1,
  'Bayer Leverkusen': 1.9,
  'RB Leipzig': 1.8,
  'Sevilla': 1.6,
  'Villarreal': 1.6,
  'Real Sociedad': 1.6,
  'Fiorentina': 1.5,
  'Lazio': 1.6,
  'Roma': 1.6,
  'Marseille': 1.6,
  'Lyon': 1.6,
  'Monaco': 1.7,
  'Porto': 1.7,
  'Benfica': 1.8,
  'Sporting CP': 1.7,
  'Ajax': 1.7,
  'PSV': 1.8,
  'Feyenoord': 1.7,
  'Galatasaray': 1.6,
  'Fenerbahce': 1.5,
  'Celtic': 1.5,
  'Rangers': 1.4,
  'Shakhtar Donetsk': 1.5,
  'Dynamo Kyiv': 1.4,
  // Clubes Brasileiros
  'Flamengo': 1.9,
  'Palmeiras': 1.8,
  'Cruzeiro': 1.8,
  'Atletico Mineiro': 1.7,
  'Sao Paulo': 1.6,
  'Fluminense': 1.6,
  'Corinthians': 1.5,
  'Internacional': 1.6,
  'Gremio': 1.5,
  'Botafogo': 1.6,
  'Bahia': 1.5,
  'Santos': 1.4,
  'Fortaleza': 1.4,
  'Atletico Goianiense': 1.3,
  'Red Bull Bragantino': 1.4,
  'Vasco da Gama': 1.3,
  'Ceara': 1.3,
  'Sport Recife': 1.2,
  'America Mineiro': 1.3,
  'Cuiaba': 1.2,
  'Goias': 1.2,
  'Chapecoense': 1.0,
  'Chapecoense-sc': 1.0,
  'Mirassol': 1.1,
  'Juventude': 1.2,
  'Vitoria': 1.2,
  'Operario': 1.1,
  'Novorizontino': 1.2,
  'Vila Nova': 1.1,
  'CRB': 1.1,
  'Itoano': 1.0,
  'Guarani': 1.0,
  'Ponte Preta': 1.1,
  'Paysandu': 1.0,
  'Avaí': 1.1,
  'Coritiba': 1.2,
  'Botafogo-sp': 1.0
};

/**
 * Retorna o xG base de um time pela tabela de força.
 * Se o time não for encontrado, usa um fallback baseado em hash estável.
 */
function getTeamBaseXG(teamName) {
  if (!teamName) return 1.2;
  
  // Normaliza o nome do time removendo sufixos de estado (-sc, -mg, -sp, etc)
  const cleanName = teamName.replace(/-(sc|mg|sp|rj|rs|pr|ba|go|pe|ce|pa|ma|al|se|pb|rn|pi|am|ap|rr|ro|ac|ms|mt|to|df)$/i, '').trim();
  
  // Busca exata no nome original ou no limpo
  if (TEAM_STRENGTH[cleanName] !== undefined) return TEAM_STRENGTH[cleanName];
  if (TEAM_STRENGTH[teamName] !== undefined) return TEAM_STRENGTH[teamName];
  
  // Busca parcial (case-insensitive)
  const upperClean = cleanName.toUpperCase();
  const upperOrig = teamName.toUpperCase();
  
  for (const [key, val] of Object.entries(TEAM_STRENGTH)) {
    const kUpper = key.toUpperCase();
    if (upperClean.includes(kUpper) || kUpper.includes(upperClean) || upperOrig.includes(kUpper) || kUpper.includes(upperOrig)) {
      return val;
    }
  }
  
  // Fallback: hash estável com range conservador (1.0-1.6) para times desconhecidos
  let h = 0;
  const s = upperClean;
  for (let i = 0; i < s.length; i++) {
    h = s.charCodeAt(i) + ((h << 5) - h);
  }
  h = Math.abs(h);
  return Math.round((1.0 + ((h % 7) / 10)) * 10) / 10; // range 1.0-1.6
}

/**
 * Calcula xG de confronto considerando força do time vs força do adversário.
 * Fórmula: xG = força_base * 0.85 * (1 + diferença_de_nível * 0.08)
 * Times mais fortes geram mais xG contra times mais fracos, e menos vs times fortes.
 * Range: 0.5 – 2.8 (realista para futebol de alto nível)
 */
function calcMatchXG(teamName, opponentName) {
  const teamStr = getTeamBaseXG(teamName);
  const oppStr = getTeamBaseXG(opponentName);
  const xg = teamStr * 0.85 * (1 + (teamStr - oppStr) * 0.08);
  return Math.max(0.5, Math.min(2.8, Math.round(xg * 10) / 10));
}

// Helper: classifica a data do jogo em relação a hoje (timezone de Brasília)
function getDayCategory(rawDate) {
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
  const parts = formatter.formatToParts(new Date());
  const todayStr = `${parts.find(p => p.type === 'year').value}-${parts.find(p => p.type === 'month').value}-${parts.find(p => p.type === 'day').value}`;

  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const tParts = formatter.formatToParts(tomorrow);
  const tomorrowStr = `${tParts.find(p => p.type === 'year').value}-${tParts.find(p => p.type === 'month').value}-${tParts.find(p => p.type === 'day').value}`;

  if (rawDate === todayStr) return 'HOJE';
  if (rawDate === tomorrowStr) return 'AMANHA';
  return 'OUTROS';
}

// Helper to fetch current round and fixtures from API-Sports
// Usa apenas 1-2 requisições (com cache L1+L2) em vez de 4 em cascata
async function fetchCurrentRoundFixtures(leagueId, activeSeason, nowTimestamp) {
  const roundFixturesCacheKey = `round_fixtures_${leagueId}_${activeSeason}`;
  let matches = [];
  let fromCache = false;
  let resolvedRound = null;

  // Tentar cache L1/L2 primeiro
  const cached = await getCachedData(roundFixturesCacheKey);
  if (cached) {
    return { matches: cached.data.matches || [], currentRound: cached.data.round, fromCache: true };
  }

  try {
    // Buscar a rodada atual em UMA única requisição (current=true)
    const roundUrl = `${API_HOST}/fixtures/rounds?league=${leagueId}&season=${activeSeason}&current=true`;
    const roundRes = await fetchAndLog(roundUrl, '/fixtures/rounds');
    const roundData = await roundRes.json();
    resolvedRound = roundData.response?.[0] || null;

    // Buscar as partidas da rodada atual em UMA única requisição
    let url = `${API_HOST}/fixtures?league=${leagueId}&season=${activeSeason}&timezone=America/Sao_Paulo`;
    if (resolvedRound) url += `&round=${encodeURIComponent(resolvedRound)}`;
    else url += `&next=10`; // fallback: próximos 10 jogos

    const res = await fetchAndLog(url, '/fixtures');
    const data = await res.json();

    if (!data.errors || Object.keys(data.errors).length === 0) {
      matches = (data.response || []).filter(m => !['CANC', 'PST', 'ABD', 'AWD', 'WO'].includes(m.fixture.status.short));

      // Se não havia rodada, detectar a mais próxima dos resultados
      if (!resolvedRound && matches.length > 0) {
        const now = new Date();
        let closestMatch = matches.reduce((prev, curr) =>
          Math.abs(new Date(curr.fixture.date) - now) < Math.abs(new Date(prev.fixture.date) - now) ? curr : prev
        );
        resolvedRound = closestMatch.league.round;
        if (resolvedRound) matches = matches.filter(m => m.league.round === resolvedRound);
      }
    }
  } catch (err) {
    console.warn(`[API-Sports] Erro ao buscar rodada para liga ${leagueId}:`, err);
  }

  if (matches.length > 0) {
    await setCachedData(roundFixturesCacheKey, { matches, round: resolvedRound });
  }

  return { matches, currentRound: resolvedRound, fromCache };
}

// ESTATÍSTICAS PARA BRASILEIRÃO VIA PACOTE LOCAL
async function getBrasileiraoStats() {
  const now = Date.now();
  if (memCache.stats['br'] && (now - memCache.stats['br'].timestamp) < 12 * 60 * 60 * 1000) {
    return memCache.stats['br'].data;
  }
  try {
    const standingsData = await getStandings('a');
    if (!standingsData || !standingsData.tables || !standingsData.tables[0]) return {};
    const stats = {};
    for (const entry of standingsData.tables[0].entries) {
      const played = entry.matches || 1;
      stats[entry.team.name] = {
        name: entry.team.name,
        logo: entry.team.badge,
        goalsFor: entry.goalsFor / played,
        goalsAgainst: entry.goalsAgainst / played,
        position: entry.position
      };
    }
    memCache.stats['br'] = { data: stats, timestamp: now };
    return stats;
  } catch (err) {
    return {};
  }
}

// ESTATÍSTICAS DETALHADAS DE QUALQUER LIGA VIA API-SPORTS (CLASSIFICAÇÃO)
async function getApiSportsStandings(leagueId, season) {
  const cacheKey = `standings_${leagueId}_${season}`;
  const now = Date.now();
  // L1 memory cache (12h)
  if (memCache.stats[cacheKey] && (now - memCache.stats[cacheKey].timestamp) < 12 * 60 * 60 * 1000) {
    return memCache.stats[cacheKey].data;
  }
  // L2 Supabase cache (12h)
  const cached = await getCachedData(cacheKey);
  if (cached) {
    memCache.stats[cacheKey] = { data: cached.data, timestamp: now };
    return cached.data;
  }
  
  try {
    const url = `${API_HOST}/standings?league=${leagueId}&season=${season}`;
    const res = await fetchAndLog(url, '/standings');
    const data = await res.json();
    const standings = data.response?.[0]?.league?.standings?.[0] || [];
    
    const stats = {};
    for (const entry of standings) {
      const teamName = entry.team.name;
      const played = entry.all.played || 1;
      stats[teamName] = {
        name: teamName,
        logo: entry.team.logo,
        goalsFor: entry.all.goals.for / played,
        goalsAgainst: entry.all.goals.against / played,
        position: entry.rank
      };
    }
    
    memCache.stats[cacheKey] = { data: stats, timestamp: now };
    // Salva no Supabase com TTL de 12h (verificado na leitura)
    await setCachedData(cacheKey, stats);
    return stats;
  } catch (err) {
    console.warn(`[API-Sports Standings] Falha ao carregar classificação da liga ${leagueId}:`, err);
    return {};
  }
}

// Reusable helper to fetch scraped fixtures for Brasileirão A and B
async function fetchScraperFixtures(leagueId, targetDate, returnAll = false) {
  try {
    const currentRoundData = await getCurrentRound(leagueId === '71' ? 'a' : 'b');
    if (!currentRoundData || !currentRoundData.rounds || currentRoundData.rounds.length === 0) {
      return { fixtures: [], round: '?' };
    }

    const activeRound = currentRoundData.rounds[0];
    const fixtures = activeRound.matches || [];
    const teamStats = await getBrasileiraoStats();

    const formattedFixtures = fixtures.map((m) => {
      const homeStats = teamStats[m.homeTeam.name] || { goalsFor: 1.2, goalsAgainst: 1.0, position: 10 };
      const awayStats = teamStats[m.awayTeam.name] || { goalsFor: 1.0, goalsAgainst: 1.2, position: 11 };

      const homeXG = Math.round(((homeStats.goalsFor + awayStats.goalsAgainst) / 2) * 10) / 10;
      const awayXG = Math.round(((awayStats.goalsFor + homeStats.goalsAgainst) / 2) * 10) / 10;

      const isLive = m.statusCode === 'LIVE' || m.status === 'live';
      const isFinished = m.statusCode === 'ENCERRADO' || m.status === 'finished' || m.status === 'ended';
      let statusLabel = isLive ? 'Em Andamento ⚽' : isFinished ? 'Finalizado' : 'Não Iniciado';

      return {
        id: m.id,
        homeTeamId: null,
        awayTeamId: null,
        date: (() => {
          const dateObj = new Date(`${m.date}T${m.time}:00-03:00`);
          const localDateStr = dateObj.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo', day: '2-digit', month: 'short' }).replace('.', '');
          return `${localDateStr} • ${m.time}`;
        })(),
        rawDate: m.date,
        dayCategory: getDayCategory(m.date),
        round: activeRound.number || '?',
        home: m.homeTeam.name,
        away: m.awayTeam.name,
        homeLogo: m.homeTeam.badge,
        awayLogo: m.awayTeam.badge,
        homeXG,
        awayXG,
        goalsHome: m.score.home,
        goalsAway: m.score.away,
        status: statusLabel,
        isLive,
        isFinished,
        minute: isLive ? 45 : 0,
        venue: m.venue || '',
        homePosition: homeStats.position,
        awayPosition: awayStats.position,
        sourceLeagueId: String(leagueId),
        league: leagueId === '71' ? 'Brasileirão Série A' : 'Brasileirão Série B',
        referee: ''
      };
    });

    const filtered = returnAll ? formattedFixtures : formattedFixtures.filter(f => f.rawDate === targetDate);
    return { fixtures: filtered, round: activeRound.number };
  } catch (err) {
    console.error(`[Scraper Helper] Erro ao buscar/formatar rodada para liga ${leagueId}:`, err);
    return { fixtures: [], round: '?' };
  }
}

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const leagueId = searchParams.get('league') || '71';
    const targetRound = searchParams.get('round');
    const isLiveOnly = searchParams.get('live') === 'true' || searchParams.get('status') === 'live';
    
    // Get target date or default to today's date in America/Sao_Paulo timezone
    const targetDate = searchParams.get('date') || (() => {
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
      return `${year}-${month}-${day}`;
    })();

    // ── BUSCA DIRETA DE JOGOS AO VIVO (LIVE=ALL) ──────────────────────────────────
    if (isLiveOnly) {
      try {
        const url = `${API_HOST}/fixtures?live=all&timezone=America/Sao_Paulo`;
        const res = await fetchAndLog(url, '/fixtures-live');
        const data = await res.json();
        const rawList = data.response || [];

        const ALLOWED_LEAGUE_IDS = [
          71, 72, 75, 76, 73, 475, 476, 604, 609, 602,
          13, 12, 11, 44, 128, 169, 281, 350, 242, 268, 274, 344, 357, 262,
          94, 88, 89, 144, 203, 179, 197, 218, 113, 103, 119, 235, 333, 332, 172,
          2, 3, 848, 531, 253, 1, 4, 5, 10, 667, 15, 29, 32, 292, 307, 188, 17
        ];

        const formatted = rawList
          .filter(m => m.fixture && m.league && ALLOWED_LEAGUE_IDS.includes(Number(m.league.id)))
          .map((m) => {
            const isFinished = ['FT', 'AET', 'PEN'].includes(m.fixture.status.short);
            const isLive = ['1H', 'HT', '2H', 'ET', 'BT', 'P', 'SUSP', 'INT', 'LIVE', 'INPLAY'].includes(m.fixture.status.short);
            const statusLabel = isLive ? `Em Andamento ⚽ ${m.fixture.status.elapsed}'` : isFinished ? 'Finalizado' : 'Não Iniciado';
            const homeXG = calcMatchXG(m.teams.home.name, m.teams.away.name);
            const awayXG = calcMatchXG(m.teams.away.name, m.teams.home.name);
            const dateObj = new Date(m.fixture.date);
            const localTimeStr = dateObj.toLocaleTimeString('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit' });
            const localDateStr = dateObj.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo', day: '2-digit', month: 'short' }).replace('.', '');

            return {
              id: m.fixture.id,
              homeTeamId: m.teams.home.id,
              awayTeamId: m.teams.away.id,
              date: `${localDateStr} • ${localTimeStr}`,
              rawDate: targetDate,
              dayCategory: 'hoje',
              round: m.league.round ? m.league.round.replace('Regular Season - ', '') : '?',
              home: m.teams.home.name,
              away: m.teams.away.name,
              homeLogo: m.teams.home.logo,
              awayLogo: m.teams.away.logo,
              homeXG,
              awayXG,
              goalsHome: m.goals.home ?? 0,
              goalsAway: m.goals.away ?? 0,
              status: statusLabel,
              isLive: true,
              isFinished: false,
              minute: m.fixture.status.elapsed || 0,
              venue: m.fixture.venue?.name || '',
              homePosition: '-',
              awayPosition: '-',
              sourceLeagueId: String(m.league.id),
              league: m.league.name
            };
          });

        return NextResponse.json({ fixtures: formatted, count: formatted.length, isLiveEndpoint: true });
      } catch (err) {
        console.warn('[API-Sports] Erro ao buscar live fixtures:', err);
      }
    }

    const season = process.env.API_FOOTBALL_SEASON || '2024';
    const isPaidPlan = season === '2026';
    const returnAll = searchParams.get('all') === 'true' || !!targetRound;

    // Determinar a temporada ativa correspondente com base no ano da data de destino
    const dateObj = new Date(targetDate + 'T00:00:00-03:00');
    const targetYear = dateObj.getFullYear();
    const targetMonth = dateObj.getMonth();

    if (leagueId === 'all') {
      let matches = [];
      let fromCache = false;
      const fixturesCacheKey = `date_${targetDate}`;
      const nowTimestamp = Date.now();

      // Verificar cache L1 + L2 antes de chamar a API
      const cachedDateFixtures = await getCachedData(fixturesCacheKey);
      if (cachedDateFixtures) {
        matches = cachedDateFixtures.data;
        fromCache = true;
      } else if (await isBudgetExceeded()) {
        // Orçamento excedido ou bloqueado manual -> busca do cache antigo ou retorna vazio sem estourar API
        matches = memCache.fixtures[fixturesCacheKey]?.data || [];
        fromCache = true;
        console.log(`[Budget Guard] All leagues request bypassed to cache.`);
      } else {
        try {
          const url = `${API_HOST}/fixtures?date=${targetDate}&timezone=America/Sao_Paulo`;
          const res = await fetchAndLog(url, '/fixtures');
          const data = await res.json();
          if (data.errors && Object.keys(data.errors).length > 0) {
            console.error(`[API-Sports] Erro retornado pela API para a data ${targetDate}:`, data.errors);
          }
          const ALLOWED_LEAGUE_IDS = [
            // Brasil
            71, 72, 75, 76, 73, 475, 476, 604, 609, 602,
            // Sul-Americanas e Américas
            13, 12, 11, 44, 128, 169, 281, 350, 242, 268, 274, 344, 357, 262,
            // Europa - Demais
            94, 88, 89, 144, 203, 179, 197, 218, 113, 103, 119, 235, 333, 332, 172,
            // Competições Europeias
            2, 3, 848, 531,
            // América do Norte
            253,
            // Internacionais
            1, 4, 5, 10, 667, 15, 29, 32,
            // Ásia e Outras
            292, 307, 188, 17
          ];
          matches = (data.response || []).filter(m => {
            if (!m.fixture || !m.league) return false;
            if (['CANC', 'ABD', 'AWD', 'WO'].includes(m.fixture.status.short)) return false;
            const lid = m.league.id;
            if (lid && ALLOWED_LEAGUE_IDS.includes(Number(lid))) return true;
            const name = String(m.league.name || '').toLowerCase();
            if (name.includes('copa do mundo')) return true;
            if (name.includes('libertadores')) return true;
            if (name.includes('sudamericana') || name.includes('sulamericana')) return true;
            if (name.includes('série a') || name.includes('serie a')) return true;
            if (name.includes('série b') || name.includes('serie b')) return true;
            if (name.includes('premier')) return true;
            if (name.includes('la liga')) return true;
            if (name.includes('bundesliga')) return true;
            if (name.includes('europa league')) return true;
            if (name.includes('conference league')) return true;
            if (name.includes('argentina')) return true;
            if (name.includes('portugal')) return true;
            return false;
          });
          // Salvar no cache L1 + L2
          await setCachedData(fixturesCacheKey, matches);
        } catch (err) {
          console.warn(`[API-Sports] Erro ao buscar fixtures da data ${targetDate}:`, err);
          matches = memCache.fixtures[fixturesCacheKey]?.data || [];
          fromCache = !!memCache.fixtures[fixturesCacheKey];
        }
      }

      // Check if we need scraper fallbacks for Série A and B
      const hasLeague71 = matches.some(m => String(m.league?.id) === '71');
      const hasLeague72 = matches.some(m => String(m.league?.id) === '72');

      const needScraper71 = !isPaidPlan || !hasLeague71;
      const needScraper72 = !isPaidPlan || !hasLeague72;

      // Filter out matches of 71 or 72 if we will fetch them from scraper instead (e.g. wrong season or empty)
      let filteredApiMatches = matches;
      if (needScraper71 || needScraper72) {
        filteredApiMatches = matches.filter(m => {
          const lid = String(m.league?.id);
          if (lid === '71' && needScraper71) return false;
          if (lid === '72' && needScraper72) return false;
          return true;
        });
      }

      const formattedFixtures = filteredApiMatches.map((m) => {
        const isFinished = ['FT', 'AET', 'PEN'].includes(m.fixture.status.short);
        const isLive = ['1H', 'HT', '2H', 'ET', 'BT', 'P', 'SUSP', 'INT', 'LIVE', 'INPLAY'].includes(m.fixture.status.short);
        let statusLabel = isLive ? `Em Andamento ⚽ ${m.fixture.status.elapsed}'` : isFinished ? 'Finalizado' : 'Não Iniciado';

        // xG calculado com base na força real de cada time (tabela TEAM_STRENGTH + fator do adversário)
        const homeXG = calcMatchXG(m.teams.home.name, m.teams.away.name);
        const awayXG = calcMatchXG(m.teams.away.name, m.teams.home.name);

        const dateObj = new Date(m.fixture.date);
        const localDateStr = dateObj.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo', day: '2-digit', month: 'short' }).replace('.', '');
        const localTimeStr = dateObj.toLocaleTimeString('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit' });
        const displayDate = `${localDateStr} • ${localTimeStr}`;

        const rawDate = (() => {
          const formatter = new Intl.DateTimeFormat('en-US', {
            timeZone: 'America/Sao_Paulo',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
          });
          const parts = formatter.formatToParts(dateObj);
          const year = parts.find(p => p.type === 'year').value;
          const month = parts.find(p => p.type === 'month').value;
          const day = parts.find(p => p.type === 'day').value;
          return `${year}-${month}-${day}`;
        })();

        return {
          id: m.fixture.id,
          homeTeamId: m.teams.home.id,
          awayTeamId: m.teams.away.id,
          date: displayDate,
          rawDate: rawDate,
          dayCategory: getDayCategory(rawDate),
          round: m.league.round ? m.league.round.replace('Regular Season - ', '') : '?',
          home: m.teams.home.name,
          away: m.teams.away.name,
          homeLogo: m.teams.home.logo,
          awayLogo: m.teams.away.logo,
          homeXG,
          awayXG,
          goalsHome: m.goals.home ?? 0,
          goalsAway: m.goals.away ?? 0,
          status: statusLabel,
          isLive,
          isFinished,
          minute: m.fixture.status.elapsed || 0,
          venue: m.fixture.venue?.name || '',
          homePosition: '-',
          awayPosition: '-',
          sourceLeagueId: String(m.league.id)
        };
      });

      // Merge scraper matches
      if (needScraper71) {
        const scraperRes = await fetchScraperFixtures('71', targetDate, returnAll);
        formattedFixtures.push(...scraperRes.fixtures);
      }
      if (needScraper72) {
        const scraperRes = await fetchScraperFixtures('72', targetDate, returnAll);
        formattedFixtures.push(...scraperRes.fixtures);
      }

      return NextResponse.json({ 
        fixtures: formattedFixtures, 
        round: 'Várias',
        season: targetYear,
        fromCache: fromCache 
      });
    }

    let activeSeason = String(targetYear);
    const europeanLeagues = ['39', '140', '135', '78'];
    if (europeanLeagues.includes(leagueId)) {
      if (targetMonth < 6) { // Antes de julho, a temporada europeia ativa ainda é a do ano anterior (e.g. 2025 para maio de 2026)
        activeSeason = String(targetYear - 1);
      } else {
        activeSeason = String(targetYear);
      }
    }

    // Para Brasileirão (Ligas 71/72), se não for plano pago (temporada 2026),
    // ou se for plano pago mas a API falhar/retornar vazio, usamos o scraper campeonato-brasileiro-api.
    let useScraper = (leagueId === '71' || leagueId === '72') && !isPaidPlan;
    let apiSportsFixtures = [];
    let fromCache = false;

    // Cache key for fixtures of the league and season
    const fixturesCacheKey = `${leagueId}_${activeSeason}`;
    const nowTimestamp = Date.now();

    if ((leagueId === '71' || leagueId === '72') && isPaidPlan) {
      let matchesOfSeason = [];
      if (returnAll) {
        const result = await fetchCurrentRoundFixtures(leagueId, activeSeason, nowTimestamp);
        matchesOfSeason = result.matches;
        fromCache = result.fromCache;
      } else {
        const leagueDateCacheKey = `league_${leagueId}_date_${targetDate}`;
        const cachedSeason = await getCachedData(leagueDateCacheKey);
        if (cachedSeason) {
          matchesOfSeason = cachedSeason.data;
          fromCache = true;
        } else if (await isBudgetExceeded()) {
          matchesOfSeason = memCache.fixtures[leagueDateCacheKey]?.data || [];
          fromCache = true;
          console.log(`[Budget Guard] Brasileirão API request bypassed to cache.`);
        } else {
          try {
            let url = `${API_HOST}/fixtures?league=${leagueId}&season=${activeSeason}&date=${targetDate}&timezone=America/Sao_Paulo`;
            let res = await fetchAndLog(url, '/fixtures');
            let data = await res.json();

            // Se retornar vazio para a temporada 2026, tenta buscar diretamente por data da liga
            if ((!data.response || data.response.length === 0) && !data.errors?.rateLimit) {
              url = `${API_HOST}/fixtures?league=${leagueId}&date=${targetDate}&timezone=America/Sao_Paulo`;
              res = await fetchAndLog(url, '/fixtures');
              data = await res.json();
            }

            matchesOfSeason = (data.response || []).filter(m => !['CANC', 'PST', 'ABD', 'AWD', 'WO'].includes(m.fixture.status.short));
            await setCachedData(leagueDateCacheKey, matchesOfSeason);
          } catch (err) {
            console.warn(`[API-Sports] Erro ao buscar Brasileirão da API:`, err);
            matchesOfSeason = memCache.fixtures[leagueDateCacheKey]?.data || [];
            fromCache = !!memCache.fixtures[leagueDateCacheKey];
          }
        }
      }

      if (matchesOfSeason.length > 0) {
        apiSportsFixtures = matchesOfSeason;
      } else {
        console.log(`[API-Sports] Nenhum jogo retornado para Brasileirão liga ${leagueId} temporada ${activeSeason}. Usando fallback Scraper...`);
        useScraper = true;
      }
    }

    if (useScraper) {
      const result = await fetchScraperFixtures(leagueId, targetDate, returnAll);
      return NextResponse.json({ 
        fixtures: result.fixtures, 
        round: result.round,
        season: 2026,
        fromCache: false 
      });
    }

    // ==========================================
    // TODAS AS LIGAS (REGRA ÚNICA BASEADA EM DATA)
    // ==========================================
    let matches = [];
    if (apiSportsFixtures.length > 0) {
      matches = apiSportsFixtures;
    } else {
      if (targetRound) {
        // Busca partidas de uma rodada específica na API-Sports
        const roundQuery = isNaN(targetRound) ? targetRound : `Regular Season - ${targetRound}`;
        const roundCacheKey = `league_${leagueId}_round_${targetRound}_${activeSeason}`;
        const cachedRound = await getCachedData(roundCacheKey);
        if (cachedRound) {
          matches = cachedRound.data;
          fromCache = true;
        } else {
          try {
            const url = `${API_HOST}/fixtures?league=${leagueId}&season=${activeSeason}&round=${encodeURIComponent(roundQuery)}&timezone=America/Sao_Paulo`;
            const res = await fetchAndLog(url, '/fixtures');
            const data = await res.json();
            matches = (data.response || []).filter(m => !['CANC', 'PST', 'ABD', 'AWD', 'WO'].includes(m.fixture.status.short));
            await setCachedData(roundCacheKey, matches);
          } catch (err) {
            console.warn(`[API-Sports] Erro ao buscar rodada ${targetRound}:`, err);
          }
        }
      } else if (returnAll) {
        const result = await fetchCurrentRoundFixtures(leagueId, activeSeason, nowTimestamp);
        matches = result.matches;
        fromCache = result.fromCache;
      } else {
        // Cache único por liga + data de destino
        const leagueDateCacheKey = `league_${leagueId}_date_${targetDate}`;
        const cachedLeagueDate = await getCachedData(leagueDateCacheKey);
        if (cachedLeagueDate) {
          matches = cachedLeagueDate.data;
          fromCache = true;
        } else if (await isBudgetExceeded()) {
          matches = memCache.fixtures[leagueDateCacheKey]?.data || [];
          fromCache = true;
          console.log(`[Budget Guard] League ${leagueId} date ${targetDate} API request bypassed to cache.`);
        } else {
          try {
            // Tenta primeiro com temporada + data
            let url = `${API_HOST}/fixtures?league=${leagueId}&season=${activeSeason}&date=${targetDate}&timezone=America/Sao_Paulo`;
            let res = await fetchAndLog(url, '/fixtures');
            let data = await res.json();

            // Se der erro ou se retornar vazio por incompatibilidade de temporada, faz a busca estrita por data da liga
            if ((!data.response || data.response.length === 0) && !data.errors?.rateLimit) {
              url = `${API_HOST}/fixtures?league=${leagueId}&date=${targetDate}&timezone=America/Sao_Paulo`;
              res = await fetchAndLog(url, '/fixtures');
              data = await res.json();
            }

            if (data.errors && Object.keys(data.errors).length > 0 && !data.response) {
              console.error(`[API-Sports] Erro retornado pela API para a liga ${leagueId} data ${targetDate}:`, data.errors);
              matches = memCache.fixtures[leagueDateCacheKey]?.data || [];
              fromCache = !!memCache.fixtures[leagueDateCacheKey];
            } else {
              matches = (data.response || []).filter(m => !['CANC', 'PST', 'ABD', 'AWD', 'WO'].includes(m.fixture.status.short));
              await setCachedData(leagueDateCacheKey, matches);
            }
          } catch (err) {
            console.warn(`[API-Sports] Erro ao buscar fixtures da liga ${leagueId} data ${targetDate}:`, err);
            matches = memCache.fixtures[leagueDateCacheKey]?.data || [];
            fromCache = !!memCache.fixtures[leagueDateCacheKey];
          }
        }
      }
    }

    // Buscar classificação (standings) da liga para calcular xG dinâmico
    const teamStats = await getApiSportsStandings(leagueId, activeSeason);

    let formattedFixtures = matches.map((m) => {
      const isFinished = ['FT', 'AET', 'PEN'].includes(m.fixture.status.short);
      const isLive = ['1H', 'HT', '2H', 'ET', 'BT', 'P', 'SUSP', 'INT', 'LIVE', 'INPLAY'].includes(m.fixture.status.short);
      let statusLabel = isLive ? `Em Andamento ⚽ ${m.fixture.status.elapsed}'` : isFinished ? 'Finalizado' : 'Não Iniciado';

      // Calcular xG dinâmico usando estatísticas da classificação (dados reais)
      // com fallback para tabela de força quando sem dados de standing
      const homeTeamName = m.teams.home.name;
      const awayTeamName = m.teams.away.name;

      const homeStats = teamStats[homeTeamName] || null;
      const awayStats = teamStats[awayTeamName] || null;

      let homeXG, awayXG;
      if (homeStats && awayStats) {
        // Ambos os times têm dados de classificação: usar xG baseado em gols reais
        homeXG = Math.round(((homeStats.goalsFor + awayStats.goalsAgainst) / 2) * 10) / 10;
        awayXG = Math.round(((awayStats.goalsFor + homeStats.goalsAgainst) / 2) * 10) / 10;
      } else if (homeStats) {
        // Apenas time da casa tem dados reais; visitante usa tabela de força
        homeXG = Math.round(homeStats.goalsFor * 10) / 10;
        awayXG = calcMatchXG(awayTeamName, homeTeamName);
      } else if (awayStats) {
        // Apenas time visitante tem dados reais; casa usa tabela de força
        homeXG = calcMatchXG(homeTeamName, awayTeamName);
        awayXG = Math.round(awayStats.goalsFor * 10) / 10;
      } else {
        // Nenhum time tem dados de standing: usar tabela de força para ambos
        homeXG = calcMatchXG(homeTeamName, awayTeamName);
        awayXG = calcMatchXG(awayTeamName, homeTeamName);
      }

      const homeStatsPos = homeStats ? homeStats.position : '-';
      const awayStatsPos = awayStats ? awayStats.position : '-';

      // Timezone-aware date formatting (Brazil timezone)
      const dateObj = new Date(m.fixture.date);
      const localDateStr = dateObj.toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo', day: '2-digit', month: 'short' }).replace('.', '');
      const localTimeStr = dateObj.toLocaleTimeString('pt-BR', { timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit' });
      const displayDate = `${localDateStr} • ${localTimeStr}`;

      // Timezone-aware rawDate in YYYY-MM-DD in America/Sao_Paulo timezone
      const rawDate = (() => {
        const formatter = new Intl.DateTimeFormat('en-US', {
          timeZone: 'America/Sao_Paulo',
          year: 'numeric',
          month: '2-digit',
          day: '2-digit'
        });
        const parts = formatter.formatToParts(dateObj);
        const year = parts.find(p => p.type === 'year').value;
        const month = parts.find(p => p.type === 'month').value;
        const day = parts.find(p => p.type === 'day').value;
        return `${year}-${month}-${day}`;
      })();

      return {
        id: m.fixture.id,
        homeTeamId: m.teams.home.id,
        awayTeamId: m.teams.away.id,
        date: displayDate,
        rawDate: rawDate,
        matchTime: localTimeStr,
        dayCategory: getDayCategory(rawDate),
        round: m.league.round ? m.league.round.replace('Regular Season - ', '') : '?',
        home: homeTeamName,
        away: awayTeamName,
        homeLogo: m.teams.home.logo,
        awayLogo: m.teams.away.logo,
        homeXG,
        awayXG,
        goalsHome: m.goals.home ?? 0,
        goalsAway: m.goals.away ?? 0,
        status: statusLabel,
        rawStatus: m.fixture.status.short,
        isLive,
        isFinished,
        minute: m.fixture.status.elapsed || 0,
        venue: m.fixture.venue?.name || '',
        homePosition: homeStatsPos,
        awayPosition: awayStatsPos,
        league: m.league.name || '',
        referee: m.fixture.referee || ''
      };
    });

    let filteredFixtures = formattedFixtures;
    let apiSportsRound = '?';

    if (returnAll) {
      if (filteredFixtures.length > 0) {
        apiSportsRound = filteredFixtures[0].round;
      }
    } else {
      // Como a consulta à API-Sports já usou &date=targetDate&timezone=America/Sao_Paulo, aceita os jogos retornados
      if (filteredFixtures.length > 0) {
        apiSportsRound = filteredFixtures[0].round;
      }
    }

    if (apiSportsRound === '?') {
      apiSportsRound = matches[0]?.league?.round?.replace('Regular Season - ', '') || '?';
    }

    return NextResponse.json({ 
      fixtures: filteredFixtures, 
      round: apiSportsRound,
      season: parseInt(activeSeason),
      fromCache: fromCache,
      apiBlocked: _apiBlockedManually || _budgetExceeded
    });

  } catch (error) {
    console.error('Fixtures API Error:', error);
    return NextResponse.json({ error: 'Erro interno do servidor' }, { status: 500 });
  }
}
