import { NextResponse } from 'next/server';

const API_KEY = process.env.API_FOOTBALL_KEY;
const API_HOST = 'https://v3.football.api-sports.io';

// Cache in-memory simple
const cache = {};
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 horas (artilheiros raramente mudam durante o dia)

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const leagueId = searchParams.get('league');
  const season = searchParams.get('season') || '2024';

  if (!leagueId) {
    return NextResponse.json({ error: 'Parâmetro league é obrigatório' }, { status: 400 });
  }

  const cacheKey = `${leagueId}_${season}`;
  const now = Date.now();

  if (cache[cacheKey] && (now - cache[cacheKey].timestamp) < CACHE_DURATION) {
    return NextResponse.json(cache[cacheKey].data);
  }

  if (!API_KEY) {
    return NextResponse.json({ error: 'Chave API_FOOTBALL_KEY não configurada' }, { status: 500 });
  }

  try {
    const url = `${API_HOST}/players/topscorers?league=${leagueId}&season=${season}`;
    const res = await fetch(url, {
      headers: {
        'x-apisports-key': API_KEY,
        'x-apisports-host': 'v3.football.api-sports.io'
      },
      next: { revalidate: 900 } // 15 minutos Next.js cache
    });

    if (!res.ok) {
      throw new Error(`Erro HTTP ${res.status}`);
    }

    const data = await res.json();
    if (data.errors && Object.keys(data.errors).length > 0) {
      return NextResponse.json({ error: 'Erro retornado pela API', details: data.errors }, { status: 502 });
    }

    const responseList = data.response || [];
    const topscorers = responseList.map(item => ({
      id: item.player.id,
      name: item.player.name,
      photo: item.player.photo,
      teamId: item.statistics?.[0]?.team?.id,
      teamName: item.statistics?.[0]?.team?.name,
      goals: item.statistics?.[0]?.goals?.total || 0,
      matches: item.statistics?.[0]?.games?.appeared || 0,
      position: item.statistics?.[0]?.games?.position || ''
    }));

    const result = { topscorers };
    cache[cacheKey] = {
      data: result,
      timestamp: now
    };

    return NextResponse.json(result);
  } catch (error) {
    console.error(`[API-Sports Topscorers] Falha ao buscar artilharia:`, error);
    return NextResponse.json({ error: 'Falha na comunicação com o servidor de dados esportivos', message: error.message }, { status: 500 });
  }
}
