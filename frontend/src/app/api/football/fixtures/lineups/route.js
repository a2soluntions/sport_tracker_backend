import { NextResponse } from 'next/server';
import { logApiCall } from '@/lib/apiLogger';

const API_KEY = process.env.API_FOOTBALL_KEY;

// Cache in-memory por partida: 15 minutos (para atualizar rápido se a escalação sair perto do jogo)
const lineupCache = {};
const CACHE_DURATION = 15 * 60 * 1000;

export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const fixtureId = searchParams.get('fixtureId') || searchParams.get('fixture');
  const homeTeam = searchParams.get('home');
  const awayTeam = searchParams.get('away');
  const homeId = searchParams.get('homeId');
  const awayId = searchParams.get('awayId');

  if (!fixtureId && !homeTeam && !awayTeam && !homeId && !awayId) {
    return NextResponse.json({ error: 'Fixture ID, team IDs, or team names required' }, { status: 400 });
  }

  const cacheKey = fixtureId ? `fixture_${fixtureId}` : `teams_${homeId || homeTeam}_${awayId || awayTeam}`;
  const now = Date.now();

  if (lineupCache[cacheKey] && (now - lineupCache[cacheKey].timestamp) < CACHE_DURATION) {
    return NextResponse.json(lineupCache[cacheKey].data);
  }

  try {
    const headers = {
      'x-apisports-key': API_KEY
    };

    let result = null;

    // 1. Tentar buscar escalação oficial confirmada via fixtureId no API-Sports
    if (fixtureId) {
      const lineupRes = await fetch(`https://v3.football.api-sports.io/fixtures/lineups?fixture=${fixtureId}`, { headers });
      const remaining = Number(lineupRes.headers.get('x-ratelimit-requests-remaining') ?? -1);
      logApiCall('/fixtures/lineups', remaining, false);

      const lineupData = await lineupRes.json();

      if (lineupData.response && lineupData.response.length >= 2) {
        const homeLineupData = lineupData.response[0];
        const awayLineupData = lineupData.response[1];

        const parsePlayers = (arr) => (arr || []).map(p => {
          const rawPos = p.player.pos || 'M';
          let posTag = 'MED';
          if (rawPos === 'G') posTag = 'GR';
          else if (rawPos === 'D') posTag = 'DEF';
          else if (rawPos === 'F' || rawPos === 'A') posTag = 'ATA';

          const nameParts = (p.player.name || '').trim().split(' ');
          const surname = nameParts.length > 1 ? nameParts[nameParts.length - 1] : nameParts[0];

          return {
            id: p.player.id,
            num: p.player.number || (posTag === 'GR' ? 1 : 10),
            pos: posTag,
            name: p.player.name || 'Jogador',
            surname: surname,
            grid: p.player.grid
          };
        });

        const homeStarters = parsePlayers(homeLineupData.startXI);
        const awayStarters = parsePlayers(awayLineupData.startXI);

        if (homeStarters.length > 0 && awayStarters.length > 0) {
          result = {
            hasRealData: true,
            isOfficial: true,
            statusLabel: '🟢 ESCALAÇÃO OFICIAL CONFIRMADA (API-SPORTS)',
            home: {
              teamName: homeLineupData.team.name,
              formation: homeLineupData.formation || '4-3-3',
              coach: homeLineupData.coach?.name || 'Técnico',
              starters: homeStarters,
              bench: parsePlayers(homeLineupData.substitutes)
            },
            away: {
              teamName: awayLineupData.team.name,
              formation: awayLineupData.formation || '4-3-3',
              coach: awayLineupData.coach?.name || 'Técnico',
              starters: awayStarters,
              bench: parsePlayers(awayLineupData.substitutes)
            }
          };
        }
      }
    }

    // 2. Se a partida não tiver escalação oficial publicada ainda, buscar o elenco ativo do clube via teamId
    if (!result && (homeId || awayId || homeTeam || awayTeam)) {
      const fetchSquadByTeam = async (tId, tName) => {
        try {
          let resolvedTeamId = tId;
          if (!resolvedTeamId && tName) {
            const searchRes = await fetch(`https://v3.football.api-sports.io/teams?search=${encodeURIComponent(tName)}`, { headers });
            const searchData = await searchRes.json();
            if (searchData.response && searchData.response.length > 0) {
              resolvedTeamId = searchData.response[0].team.id;
            }
          }

          if (!resolvedTeamId) return null;

          const squadRes = await fetch(`https://v3.football.api-sports.io/players/squads?team=${resolvedTeamId}`, { headers });
          const squadData = await squadRes.json();

          if (squadData.response && squadData.response.length > 0) {
            const players = squadData.response[0].players || [];
            const parseSquadPlayer = (p) => {
              const rawPos = p.position || 'Midfielder';
              let posTag = 'MED';
              if (rawPos === 'Goalkeeper') posTag = 'GR';
              else if (rawPos === 'Defender') posTag = 'DEF';
              else if (rawPos === 'Attacker') posTag = 'ATA';

              const nameParts = (p.name || '').trim().split(' ');
              const surname = nameParts.length > 1 ? nameParts[nameParts.length - 1] : nameParts[0];

              return {
                id: p.id,
                num: p.number || (posTag === 'GR' ? 1 : 10),
                pos: posTag,
                name: p.name,
                surname: surname
              };
            };

            const allParsed = players.map(parseSquadPlayer);

            // Agrupar e ordenar jogadores por posição funcional: 1 GR, 4 DEF, 3 MED, 3 ATA
            const goalkeepers = allParsed.filter(p => p.pos === 'GR');
            const defenders = allParsed.filter(p => p.pos === 'DEF');
            const midfielders = allParsed.filter(p => p.pos === 'MED');
            const attackers = allParsed.filter(p => p.pos === 'ATA');

            const starters = [
              ...goalkeepers.slice(0, 1),
              ...defenders.slice(0, 4),
              ...midfielders.slice(0, 3),
              ...attackers.slice(0, 3)
            ];

            const starterIds = new Set(starters.map(s => s.id));
            const bench = allParsed.filter(p => !starterIds.has(p.id)).slice(0, 7);

            return {
              teamName: tName || squadData.response[0].team.name,
              formation: '4-3-3',
              coach: 'Técnico',
              starters,
              bench
            };
          }
        } catch (e) {
          console.error(`Erro ao buscar squad para ${tName || tId}:`, e);
        }
        return null;
      };

      const homeSquad = await fetchSquadByTeam(homeId, homeTeam);
      const awaySquad = await fetchSquadByTeam(awayId, awayTeam);

      if (homeSquad || awaySquad) {
        result = {
          hasRealData: true,
          isOfficial: false,
          statusLabel: '🔵 ELENCO ATIVO OFICIAL DO CLUBE (API-SPORTS)',
          home: homeSquad || { teamName: homeTeam, formation: '4-3-3', coach: 'Técnico', starters: [], bench: [] },
          away: awaySquad || { teamName: awayTeam, formation: '4-3-3', coach: 'Técnico', starters: [], bench: [] }
        };
      }
    }

    if (result) {
      lineupCache[cacheKey] = { data: result, timestamp: now };
      return NextResponse.json(result);
    }

    return NextResponse.json({ hasRealData: false, message: 'Escalação indisponível no API-Sports no momento' }, { status: 404 });
  } catch (error) {
    console.error('API Sports Lineups Error:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
