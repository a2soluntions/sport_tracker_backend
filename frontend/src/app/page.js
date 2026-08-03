'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { 
  Zap, 
  Activity, 
  Calendar, 
  Clock, 
  Play, 
  ChevronRight, 
  Trophy, 
  Sparkles, 
  Search,
  Users
} from 'lucide-react';

const SUPPORTED_LEAGUES = [
  { id: '71', name: 'Brasileirão Série A', country: 'Brasil', logo: 'https://media.api-sports.io/football/leagues/71.png' },
  { id: '72', name: 'Brasileirão Série B', country: 'Brasil', logo: 'https://media.api-sports.io/football/leagues/72.png' },
  { id: '39', name: 'Premier League', country: 'Inglaterra', logo: 'https://media.api-sports.io/football/leagues/39.png' },
  { id: '140', name: 'La Liga', country: 'Espanha', logo: 'https://media.api-sports.io/football/leagues/140.png' },
  { id: '135', name: 'Serie A', country: 'Itália', logo: 'https://media.api-sports.io/football/leagues/135.png' },
  { id: '78', name: 'Bundesliga', country: 'Alemanha', logo: 'https://media.api-sports.io/football/leagues/78.png' },
  { id: '13', name: 'Copa Libertadores', country: 'América do Sul', logo: 'https://media.api-sports.io/football/leagues/13.png' },
  { id: '12', name: 'Copa Sudamericana', country: 'América do Sul', logo: 'https://media.api-sports.io/football/leagues/12.png' },
  { id: '3', name: 'UEFA Europa League', country: 'Europa', logo: 'https://media.api-sports.io/football/leagues/3.png' },
  { id: '667', name: 'Amistosos Internacionais', country: 'Mundo', logo: 'https://media.api-sports.io/football/leagues/667.png' }
];

export default function CentralScoreHome() {
  const router = useRouter();
  const { user } = useAuth();
  
  const [fixtures, setFixtures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentDate, setCurrentDate] = useState('');

  // Define formatador de data para o Horário de Brasília
  useEffect(() => {
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
    setCurrentDate(`${year}-${month}-${day}`);
  }, []);

  // Fetch das fixtures do dia para contar partidas por liga
  useEffect(() => {
    if (!currentDate) return;
    async function loadTodayScores() {
      try {
        setLoading(true);
        const res = await fetch(`/api/football/fixtures?league=all&date=${currentDate}`);
        if (res.ok) {
          const data = await res.json();
          if (data.fixtures) {
            setFixtures(data.fixtures);
          }
        }
      } catch (err) {
        console.warn('Erro ao carregar fixtures na tela inicial:', err);
      } finally {
        setLoading(false);
      }
    }
    loadTodayScores();
  }, [currentDate]);

  // Contabiliza jogos ativos e agendados para uma determinada liga
  const getLeagueMatchCounts = (leagueId) => {
    const leagueFixtures = fixtures.filter(f => String(f.sourceLeagueId) === String(leagueId));
    const liveCount = leagueFixtures.filter(f => f.isLive).length;
    const totalCount = leagueFixtures.length;
    const scheduledCount = leagueFixtures.filter(f => !f.isLive && !f.isFinished).length;
    const finishedCount = leagueFixtures.filter(f => f.isFinished).length;

    return {
      live: liveCount,
      scheduled: scheduledCount,
      finished: finishedCount,
      total: totalCount
    };
  };

  // Filtragem de ligas por termo de pesquisa
  const filteredLeagues = SUPPORTED_LEAGUES.filter(league => 
    league.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    league.country.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div style={{
      background: '#09090b',
      color: '#fafafa',
      fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      minHeight: '100vh',
      width: '100%',
      overflowX: 'hidden'
    }}>
      {/* Header Premium */}
      <nav style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '18px 6%',
        background: 'rgba(9, 9, 11, 0.95)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        width: '100%'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            background: 'linear-gradient(135deg, var(--brand-neon) 0%, #00ff88 100%)',
            padding: '8px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(204, 255, 0, 0.25)'
          }}>
            <Zap size={22} color="#000" strokeWidth={2.5} fill="#000" />
          </div>
          <span style={{ fontWeight: 950, fontSize: '1.4rem', letterSpacing: '-0.8px', color: '#fff' }}>
            A2SPORT<span style={{ color: 'var(--brand-neon)' }}>TRACKERS</span>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {user ? (
            <Link href="/admin" style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: '#fff',
              padding: '8px 18px',
              borderRadius: '8px',
              fontSize: '0.88rem',
              fontWeight: 'bold',
              textDecoration: 'none',
              transition: 'all 0.2s'
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
            >
              Painel Admin
            </Link>
          ) : (
            <Link href="/login" style={{
              background: 'var(--brand-neon)',
              color: '#000',
              padding: '8px 20px',
              borderRadius: '8px',
              fontSize: '0.88rem',
              fontWeight: 'bold',
              textDecoration: 'none',
              transition: 'opacity 0.2s',
              boxShadow: '0 0 15px rgba(204, 255, 0, 0.3)'
            }}
            onMouseEnter={e => e.currentTarget.style.opacity = '0.9'}
            onMouseLeave={e => e.currentTarget.style.opacity = '1'}
            >
              Entrar no SaaS
            </Link>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <header style={{
        padding: '70px 6% 40px 6%',
        textAlign: 'center',
        background: 'radial-gradient(circle at 50% 10%, rgba(204, 255, 0, 0.06) 0%, transparent 60%)',
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(204, 255, 0, 0.08)',
          border: '1px solid rgba(204, 255, 0, 0.2)',
          padding: '6px 14px',
          borderRadius: '50px',
          color: 'var(--brand-neon)',
          fontSize: '0.78rem',
          fontWeight: 'bold',
          marginBottom: '20px',
          textTransform: 'uppercase',
          letterSpacing: '1px'
        }}>
          <Sparkles size={14} /> CENTRAL DE CONTROLE & SCORE DOS CAMPEONATOS
        </div>

        <h1 style={{
          fontSize: 'clamp(2.2rem, 4.5vw, 3.6rem)',
          fontWeight: 900,
          lineHeight: 1.15,
          marginBottom: '16px',
          letterSpacing: '-1.2px',
          textTransform: 'uppercase'
        }}>
          Escolha uma Liga para <span style={{
            background: 'linear-gradient(90deg, var(--brand-neon) 0%, #00ff88 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>Iniciar as Previsões</span>
        </h1>

        <p style={{
          color: '#a1a1aa',
          fontSize: '1.1rem',
          maxWidth: '650px',
          margin: '0 auto 36px auto',
          lineHeight: 1.55
        }}>
          Acompanhe o status e a quantidade de partidas ao vivo ou agendadas. Clique em qualquer liga para analisar probabilidades de Poisson, palpites e estatísticas completas.
        </p>

        {/* Barra de Pesquisa */}
        <div style={{
          maxWidth: '550px',
          margin: '0 auto',
          position: 'relative',
          display: 'flex',
          alignItems: 'center'
        }}>
          <Search size={18} color="#71717a" style={{ position: 'absolute', left: '16px' }} />
          <input 
            type="text"
            placeholder="Buscar campeonato ou país..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              background: '#16161c',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '12px',
              padding: '14px 16px 14px 48px',
              color: '#fff',
              fontSize: '0.95rem',
              outline: 'none',
              transition: 'border-color 0.2s',
              boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
            }}
            onFocus={e => e.target.style.borderColor = 'var(--brand-neon)'}
            onBlur={e => e.target.style.borderColor = 'rgba(255, 255, 255, 0.08)'}
          />
        </div>
      </header>

      {/* Grid de Ligas */}
      <main style={{
        padding: '20px 6% 80px 6%',
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '200px', gap: '12px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              border: '3px solid rgba(204, 255, 0, 0.1)',
              borderTopColor: 'var(--brand-neon)',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }}></div>
            <span style={{ fontSize: '0.9rem', color: '#71717a' }}>Carregando dados das ligas em tempo real...</span>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '24px'
          }}>
            {filteredLeagues.map((league) => {
              const counts = getLeagueMatchCounts(league.id);

              return (
                <div 
                  key={league.id}
                  onClick={() => router.push(`/estatisticas?league=${encodeURIComponent(league.name)}`)}
                  style={{
                    background: '#121217',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    borderRadius: '16px',
                    padding: '24px',
                    cursor: 'pointer',
                    transition: 'transform 0.2s, border-color 0.2s, box-shadow 0.2s',
                    position: 'relative',
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    minHeight: '220px'
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                    e.currentTarget.style.borderColor = 'var(--brand-neon)';
                    e.currentTarget.style.boxShadow = '0 8px 30px rgba(204, 255, 0, 0.08)';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.06)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  {/* Badge Ao Vivo se tiver jogos rolando */}
                  {counts.live > 0 && (
                    <div style={{
                      position: 'absolute',
                      top: '16px',
                      right: '16px',
                      background: 'rgba(255, 68, 68, 0.1)',
                      border: '1px solid #ff4444',
                      borderRadius: '50px',
                      padding: '4px 10px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      fontSize: '0.68rem',
                      fontWeight: 'bold',
                      color: '#ff4444'
                    }}>
                      <span style={{
                        width: '6px',
                        height: '6px',
                        background: '#ff4444',
                        borderRadius: '50%',
                        display: 'inline-block',
                        animation: 'blink 1.2s infinite'
                      }}></span>
                      {counts.live} AO VIVO
                    </div>
                  )}

                  {/* Topo do Card: Info Liga */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
                      <img 
                        src={league.logo} 
                        alt={league.name}
                        style={{
                          width: '44px',
                          height: '44px',
                          objectFit: 'contain',
                          background: 'rgba(255,255,255,0.02)',
                          padding: '6px',
                          borderRadius: '8px',
                          border: '1px solid rgba(255,255,255,0.04)'
                        }}
                      />
                      <div>
                        <h3 style={{ fontSize: '1.05rem', fontWeight: 'bold', margin: 0, color: '#fff', lineHeight: '1.3' }}>
                          {league.name}
                        </h3>
                        <span style={{ fontSize: '0.78rem', color: '#71717a', display: 'block', marginTop: '2px' }}>
                          📍 {league.country}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Corpo do Card: Contadores de Partidas */}
                  <div style={{
                    background: '#16161e',
                    borderRadius: '12px',
                    padding: '12px 16px',
                    marginBottom: '16px',
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '10px',
                    border: '1px solid rgba(255, 255, 255, 0.02)'
                  }}>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: '0.7rem', color: '#71717a', textTransform: 'uppercase', fontWeight: '600' }}>Agendados</span>
                      <strong style={{ fontSize: '1.1rem', color: '#fff', marginTop: '2px' }}>{counts.scheduled}</strong>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: '0.7rem', color: '#71717a', textTransform: 'uppercase', fontWeight: '600' }}>Finalizados</span>
                      <strong style={{ fontSize: '1.1rem', color: '#a1a1aa', marginTop: '2px' }}>{counts.finished}</strong>
                    </div>
                  </div>

                  {/* Rodapé do Card: Ação */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.8rem',
                    fontWeight: 'bold',
                    color: 'var(--brand-neon)',
                    borderTop: '1px solid rgba(255,255,255,0.04)',
                    paddingTop: '12px'
                  }}>
                    <span>Análise & Previsões</span>
                    <ChevronRight size={16} />
                  </div>
                </div>
              );
            })}

            {filteredLeagues.length === 0 && (
              <div style={{
                gridColumn: '1 / -1',
                textAlign: 'center',
                padding: '40px',
                background: '#121217',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '16px',
                color: '#a1a1aa'
              }}>
                Nenhum campeonato encontrado para "{searchTerm}"
              </div>
            )}
          </div>
        )}
      </main>

      {/* Estilos Auxiliares de Keyframe */}
      <style jsx global>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </div>
  );
}
