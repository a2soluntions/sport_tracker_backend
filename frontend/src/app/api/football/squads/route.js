import { NextResponse } from 'next/server';
import { logApiCall } from '@/lib/apiLogger';

const API_KEY = process.env.API_FOOTBALL_KEY;

// Cache in-memory: 6 horas (dados de elenco mudam raramente)
const squadCache = {};
const CACHE_DURATION = 6 * 60 * 60 * 1000; // 6 horas

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const teamId = searchParams.get('teamId');
  const teamName = searchParams.get('team'); // fallback

  if (!teamId && !teamName) {
    return NextResponse.json({ error: 'Team ID or Team Name is required' }, { status: 400 });
  }

  // Check cache first (by teamId or teamName)
  const cacheKey = teamId ? `id_${teamId}` : `name_${teamName}`;
  const now = Date.now();
  if (squadCache[cacheKey] && (now - squadCache[cacheKey].timestamp) < CACHE_DURATION) {
    return NextResponse.json(squadCache[cacheKey].data);
  }

  try {
    const headers = {
      'x-apisports-key': API_KEY
    };

    let resolvedTeamId = teamId;

    // Se só passou o nome, tenta buscar o ID do time na API-Sports
    // (verificar também o cache pelo nome antes de chamar a API)
    if (!resolvedTeamId) {
      const searchRes = await fetch(`https://v3.football.api-sports.io/teams?search=${encodeURIComponent(teamName)}`, { headers });
      const searchRemaining = Number(searchRes.headers.get('x-ratelimit-requests-remaining') ?? -1);
      logApiCall('/teams', searchRemaining, false);
      const searchData = await searchRes.json();
      
      if (searchData.response && searchData.response.length > 0) {
        resolvedTeamId = searchData.response[0].team.id;
      }
    }

    if (!resolvedTeamId) {
       return NextResponse.json({ error: 'Team not found for ' + teamName }, { status: 404 });
    }

    // Verificar cache pelo ID resolvido também
    const idCacheKey = `id_${resolvedTeamId}`;
    if (squadCache[idCacheKey] && (now - squadCache[idCacheKey].timestamp) < CACHE_DURATION) {
      // Aproveitar o cache existente pelo ID e salvar também pela chave original
      if (cacheKey !== idCacheKey) {
        squadCache[cacheKey] = squadCache[idCacheKey];
      }
      return NextResponse.json(squadCache[idCacheKey].data);
    }

    // Buscar o elenco atualizado do time
    const squadRes = await fetch(`https://v3.football.api-sports.io/players/squads?team=${resolvedTeamId}`, { headers });
    const squadRemaining = Number(squadRes.headers.get('x-ratelimit-requests-remaining') ?? -1);
    logApiCall('/players/squads', squadRemaining, false);
    const squadData = await squadRes.json();

    if (!squadData.response || squadData.response.length === 0) {
      return NextResponse.json({ error: 'Squad not found' }, { status: 404 });
    }

    const players = squadData.response[0].players.map(p => ({
      id: p.id,
      name: p.name,
      age: p.age,
      number: p.number,
      position: p.position,
      photo: p.photo
    }));

    // Ordenar os atacantes primeiro, depois meio-campistas
    players.sort((a, b) => {
      const posA = a.position === 'Attacker' ? 1 : a.position === 'Midfielder' ? 2 : 3;
      const posB = b.position === 'Attacker' ? 1 : b.position === 'Midfielder' ? 2 : 3;
      return posA - posB;
    });

    const result = { players };

    // Salvar em cache por ID e pelo cacheKey original (nome ou id)
    squadCache[idCacheKey] = { data: result, timestamp: now };
    if (cacheKey !== idCacheKey) {
      squadCache[cacheKey] = { data: result, timestamp: now };
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error('API Sports Squads Error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
