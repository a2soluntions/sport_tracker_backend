'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { BookOpen, Zap, DollarSign, ShieldAlert, Award, ChevronRight, Calculator, CheckCircle2, TrendingUp, AlertTriangle, Shield, Sword, ArrowRight, ChevronLeft, ChevronRight as ChevronRightIcon } from 'lucide-react';

export default function TutorialPage() {
  const [activeCard, setActiveCard] = useState(0);

  const downloadExcelTemplate = () => {
    const htmlContent = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
      <head>
      <meta charset="utf-8">
      <style>
        table { border-collapse: collapse; }
        td { border: 0.5pt solid #333333; font-family: 'Segoe UI', Tahoma, sans-serif; font-size: 10pt; padding: 6px; }
        .brand-header { background-color: #0d0d11; color: #ccff00; font-size: 16pt; font-weight: bold; text-align: center; height: 50px; }
        .sub-header { background-color: #141419; color: #888888; font-size: 9pt; text-align: center; height: 25px; }
        .col-header { background-color: #1c1c24; color: #ffffff; font-weight: bold; text-align: center; height: 30px; }
        .formula-cell { background-color: #112211; color: #00ff00; font-weight: bold; text-align: right; }
        .num-cell { text-align: right; }
        .center-cell { text-align: center; }
        .green-text { color: #00ff00; font-weight: bold; }
        .blue-text { color: #00d2ff; font-weight: bold; }
      </style>
      </head>
      <body>
      <table>
        <tr>
          <td colspan="10" class="brand-header">A2 SPORTS TRACKER</td>
        </tr>
        <tr>
          <td colspan="10" class="sub-header">Modelo Oficial de Gestao de Banca & Entradas +EV - Download Gratuito</td>
        </tr>
        <tr>
          <td class="col-header">Data</td>
          <td class="col-header">Confronto / Jogo</td>
          <td class="col-header">Mercado</td>
          <td class="col-header">Odd da Casa</td>
          <td class="col-header">Sua Probabilidade (%)</td>
          <td class="col-header">EV (%)</td>
          <td class="col-header">Stake (R$)</td>
          <td class="col-header">Resultado</td>
          <td class="col-header">Justificativa Tecnica</td>
          <td class="col-header">Tipo</td>
        </tr>
        <tr>
          <td class="center-cell">08/07/2026</td>
          <td>Real Madrid x Barcelona</td>
          <td>Mais de 2.5 Gols</td>
          <td class="num-cell">1.95</td>
          <td class="num-cell">58</td>
          <td class="formula-cell">=((E4/100)*D4-1)*100</td>
          <td class="num-cell">100.00</td>
          <td class="center-cell blue-text">PENDENTE</td>
          <td>Poisson indica 58% vs 51.2% implicito. Valor claro no Over.</td>
          <td class="center-cell">Profissional (+EV)</td>
        </tr>
        <tr>
          <td class="center-cell">08/07/2026</td>
          <td>Bayern de Munique x Dortmund</td>
          <td>Vencedor Encontro: Bayern</td>
          <td class="num-cell">1.75</td>
          <td class="num-cell">65</td>
          <td class="formula-cell">=((E5/100)*D5-1)*100</td>
          <td class="num-cell">150.00</td>
          <td class="center-cell blue-text">PENDENTE</td>
          <td>Dominio historico em casa com retorno de jogadores chaves.</td>
          <td class="center-cell">Profissional (+EV)</td>
        </tr>
        <tr>
          <td class="center-cell">08/07/2026</td>
          <td>Exemplo Lucrativo</td>
          <td>Seu Mercado Aqui</td>
          <td class="num-cell">2.10</td>
          <td class="num-cell">52</td>
          <td class="formula-cell">=((E6/100)*D6-1)*100</td>
          <td class="num-cell">50.00</td>
          <td class="center-cell green-text">GANHO</td>
          <td>Insira sua justificativa de precificacao nesta coluna.</td>
          <td class="center-cell">Profissional (+EV)</td>
        </tr>
      </table>
      </body>
      </html>
    `;

    const blob = new Blob([htmlContent], { type: 'application/vnd.ms-excel;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "A2SportsTracker_Planilha_EV_Oficial.xls");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const cardsMethod = [
    {
      title: "Guia do Avaliador de Apostas",
      subtitle: "Validade e Métodos",
      number: "INTRO",
      color: "var(--brand-neon)",
      desc: "O objetivo profissional não deve ser acertar placares por intuição, mas sim encontrar odds de valor. 90% de chance implícita (ex: odd 1.05) é péssimo se o risco não compensar o evento."
    },
    {
      title: "1. Odds e o Inimigo Invisível",
      subtitle: "Taxas do Mercado",
      number: "CAP 01",
      color: "#00d2ff",
      desc: "As odds representam a probabilidade implícita calculada por softwares. A fórmula é P = (1 / Odd) * 100. A soma das probabilidades (Casa + Empate + Fora) sempre supera 100% devido ao Juice (taxa invisível da casa)."
    },
    {
      title: "2. Valor Esperado (+EV)",
      subtitle: "+EV",
      number: "CAP 02",
      color: "#ff9800",
      desc: "Aposte apenas quando a probabilidade real for maior que a implícita da casa. EV = (Prob. Real * Lucro) - (Prob. Perder * Stake). Evite volatilidade extrema (odd ideal entre 1.60 e 2.00)."
    },
    {
      title: "3. Gestão de Banca",
      subtitle: "Escudo Financeiro",
      number: "CAP 03",
      color: "#4CAF50",
      desc: "Divida sua banca em Unidades (ex: R$ 100 = 100 U). Use de 1% (conservador) a 2% (moderado) por entrada. Evite múltiplas e prefira simples com proteções como HA +0.25."
    },
    {
      title: "4. Registros e Proteções",
      subtitle: "Paper Trading & Planilha",
      number: "CAP 04",
      color: "#e5a3ff",
      desc: "Documente tudo em planilha. Colunas obrigatórias: data, mercado, odd da casa, sua probabilidade, EV, stake e resultado (com justificativa). A fórmula ativa do EV exportada é: =((Probabilidade/100)*Odd - 1)*100. Baixe sua planilha com fórmulas dinâmicas diretamente na aba de Gestão de Banca!"
    },
    {
      title: "Camada Avançada",
      subtitle: "Modelagem de Elite",
      number: "CAP 05",
      color: "#ff5555",
      desc: "Aplique a Lei de Probabilidade Total para precificar gols e escanteios. Use o Critério de Kelly para otimizar stakes com +EV provado. Faça Paper Trading para avaliar a Closing Line Value (CLV)."
    },
    {
      title: "Motor: Distribuição de Poisson",
      subtitle: "Modelo Estatístico",
      number: "MATEMÁTICA",
      color: "#ffd93d",
      desc: "Use força de ataque e defesa dos times (30 jogos) para calcular médias de gols. A fórmula de Poisson calcula chances exatas por placar. A odd justa é obtida dividindo 100 pela soma dessas chances."
    },
    {
      title: "Documento Mestre — Resumo",
      subtitle: "Prática Diária",
      number: "RESUMO",
      color: "var(--brand-neon)",
      desc: "Domine odds e juice, selecione palpites +EV entre 1.60 e 2.00, proteja com gestão de banca de 1% a 2% e anote tudo. Salve este resumo no seu Bloco de Notas ou PDF para consulta diária."
    }
  ];
  return (
    <div style={{
      padding: '20px',
      maxWidth: '1000px',
      margin: '0 auto',
      width: '100%',
      fontFamily: 'Outfit, system-ui, sans-serif'
    }}>
      {/* Header Section */}
      <div style={{ marginBottom: '40px', borderBottom: '1px solid #1f1f2e', paddingBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--brand-neon)', marginBottom: '12px' }}>
            <BookOpen size={28} />
            <span style={{ fontSize: '0.9rem', fontWeight: 'bold', letterSpacing: '2px', textTransform: 'uppercase' }}>Central de Aprendizado</span>
          </div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 900, textTransform: 'uppercase', lineHeight: 1.2 }}>
            Como Entender Odds e Proteger seu Dinheiro
          </h1>
          <p style={{ color: '#888', marginTop: '12px', fontSize: '1.1rem', maxWidth: '800px', lineHeight: 1.6 }}>
            Evolua de um apostador recreativo para um investidor esportivo profissional. Aprenda a pensar de forma lógica, dominar a matemática do mercado e utilizar o nosso sistema da maneira mais lucrativa possível.
          </p>
        </div>

        {/* Introduction Warning Banner */}
        <div style={{
          background: 'rgba(204, 255, 0, 0.03)',
          border: '1px solid rgba(204, 255, 0, 0.2)',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '40px',
          display: 'flex',
          gap: '16px',
          alignItems: 'flex-start'
        }}>
          <Award size={32} style={{ color: 'var(--brand-neon)', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h3 style={{ fontWeight: 'bold', fontSize: '1.1rem', color: '#fff', marginBottom: '8px' }}>MINDSET PROFISSIONAL</h3>
            <p style={{ color: '#aaa', fontSize: '0.95rem', lineHeight: 1.6, margin: 0 }}>
              Casas de apostas lucram com a emoção e com a falta de método dos usuários. O segredo para vencer no longo prazo não é adivinhar placares por intuição, mas sim encontrar <strong>desajustes matemáticos</strong> e aplicar uma gestão de capital blindada contra a ruína.
            </p>
          </div>
        </div>

        {/* INTERACTIVE METHODOLOGY FLASHCARDS (CARDS DO SISTEMA) */}
        <div style={{
          background: 'linear-gradient(180deg, #111116 0%, #070709 100%)',
          border: '1px solid rgba(255,255,255,0.03)',
          borderRadius: '20px',
          padding: '28px',
          marginBottom: '48px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.6)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, textTransform: 'uppercase', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Zap size={22} color="var(--brand-neon)" />
                Cards do Método Profissional
              </h2>
              <p style={{ margin: '4px 0 0 0', fontSize: '0.82rem', color: '#666' }}>Guia Prático Rápido e Resumos do Avaliador de Apostas</p>
            </div>
            
            {/* Control buttons */}
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setActiveCard(prev => (prev === 0 ? cardsMethod.length - 1 : prev - 1))}
                style={{
                  background: '#161622',
                  border: '1px solid #222',
                  color: '#fff',
                  borderRadius: '8px',
                  width: '38px',
                  height: '38px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--brand-neon)'}
                onMouseOut={(e) => e.currentTarget.style.borderColor = '#222'}
              >
                <ChevronLeft size={20} />
              </button>
              <button
                onClick={() => setActiveCard(prev => (prev === cardsMethod.length - 1 ? 0 : prev + 1))}
                style={{
                  background: '#161622',
                  border: '1px solid #222',
                  color: '#fff',
                  borderRadius: '8px',
                  width: '38px',
                  height: '38px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.borderColor = 'var(--brand-neon)'}
                onMouseOut={(e) => e.currentTarget.style.borderColor = '#222'}
              >
                <ChevronRightIcon size={20} />
              </button>
            </div>
          </div>

          {/* Main Flashcard display */}
          <div style={{
            background: 'radial-gradient(circle at 80% 20%, rgba(204, 255, 0, 0.05) 0%, transparent 80%), #0d0d12',
            border: '2px solid ' + cardsMethod[activeCard].color,
            borderRadius: '16px',
            padding: '32px',
            minHeight: '220px',
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            boxShadow: '0 10px 30px rgba(0,0,0,0.8), inset 0 0 40px rgba(0,0,0,0.9)',
            overflow: 'hidden'
          }}>
            {/* Background design */}
            <div style={{
              position: 'absolute',
              top: '5%',
              right: '5%',
              fontSize: '4.5rem',
              fontWeight: 900,
              color: 'rgba(255,255,255,0.01)',
              userSelect: 'none',
              lineHeight: 1
            }}>
              {cardsMethod[activeCard].number}
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.68rem', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '2px', color: cardsMethod[activeCard].color }}>
                  {cardsMethod[activeCard].subtitle}
                </span>
                <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#444' }} />
                <span style={{ fontSize: '0.68rem', fontWeight: 'bold', color: '#666' }}>
                  {activeCard + 1} de {cardsMethod.length}
                </span>
              </div>
              <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, textTransform: 'uppercase', color: '#fff', letterSpacing: '0.5px' }}>
                {cardsMethod[activeCard].title}
              </h3>
              <p style={{ margin: '16px 0 0 0', fontSize: '1.05rem', color: '#ccc', lineHeight: '1.6', maxWidth: '780px' }}>
                {cardsMethod[activeCard].desc}
              </p>
            </div>
          </div>

          {/* Quick thumbnails navigation */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(95px, 1fr))',
            gap: '8px',
            marginTop: '16px'
          }}>
            {cardsMethod.map((item, idx) => (
              <button
                key={idx}
                onClick={() => setActiveCard(idx)}
                style={{
                  background: activeCard === idx ? 'rgba(204,255,0,0.05)' : '#0d0d12',
                  border: '1px solid ' + (activeCard === idx ? item.color : '#222'),
                  borderRadius: '8px',
                  padding: '10px 8px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  transition: 'all 0.2s',
                  minHeight: '62px'
                }}
              >
                <span style={{ fontSize: '0.6rem', color: '#555', fontWeight: 'bold' }}>{item.number}</span>
                <span style={{
                  fontSize: '0.72rem',
                  fontWeight: 'bold',
                  color: activeCard === idx ? '#fff' : '#888',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  width: '100%'
                }} title={item.title}>
                  {item.title.replace(/^\d+\.\s*/, '')}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Tutorial Chapters Grid */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '48px' }}>
          
          {/* 1. O que realmente são as odds? */}
          <section style={{ scrollMarginTop: '80px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: '#1c1c24', color: 'var(--brand-neon)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center' }}>
                <Calculator size={22} />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, textTransform: 'uppercase' }}>1. O que Realmente são as Odds?</h2>
            </div>
            
            <p style={{ color: '#aaa', lineHeight: 1.6, marginBottom: '20px' }}>
              As odds não são apenas multiplicadores de lucro definidos ao acaso. Elas representam a <strong>Probabilidade Implícita</strong> que a casa de apostas calculou para aquele resultado acontecer. A fórmula matemática para extrair essa porcentagem é:
            </p>

            <div style={{
              background: '#141416',
              border: '1px solid #222',
              borderRadius: '12px',
              padding: '20px',
              textAlign: 'center',
              margin: '24px 0',
              fontFamily: 'monospace'
            }}>
              <span style={{ fontSize: '1.4rem', color: 'var(--brand-neon)', fontWeight: 'bold' }}>
                Probabilidade Implícita (%) = (1 / Odd) × 100
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginBottom: '20px' }}>
              <div style={{ background: '#141416', padding: '16px', border: '1px solid #222', borderRadius: '8px' }}>
                <span style={{ color: 'var(--brand-neon)', fontWeight: 'bold' }}>Odd de 1.60</span>
                <p style={{ color: '#888', fontSize: '0.9rem', marginTop: '6px', margin: 0 }}>(1 / 1.60) × 100 = <strong>62,5%</strong> de chance implícita.</p>
              </div>
              <div style={{ background: '#141416', padding: '16px', border: '1px solid #222', borderRadius: '8px' }}>
                <span style={{ color: 'var(--brand-neon)', fontWeight: 'bold' }}>Odd de 2.00</span>
                <p style={{ color: '#888', fontSize: '0.9rem', marginTop: '6px', margin: 0 }}>(1 / 2.00) × 100 = <strong>50,0%</strong> de chance implícita.</p>
              </div>
              <div style={{ background: '#141416', padding: '16px', border: '1px solid #222', borderRadius: '8px' }}>
                <span style={{ color: '#ff5555', fontWeight: 'bold' }}>Odd de 35.00 (Múltipla Pronta)</span>
                <p style={{ color: '#888', fontSize: '0.9rem', marginTop: '6px', margin: 0 }}>(1 / 35.00) × 100 = apenas <strong>2,85%</strong> de chance real de acerto.</p>
              </div>
            </div>

            <div style={{ background: 'rgba(255, 152, 0, 0.03)', border: '1px dashed rgba(255, 152, 0, 0.3)', borderRadius: '12px', padding: '16px' }}>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center', color: '#ff9800', marginBottom: '6px', fontWeight: 'bold', fontSize: '0.9rem' }}>
                <AlertTriangle size={16} />
                <span>O LUCRO OCULTO (JUICE / VIG)</span>
              </div>
              <p style={{ color: '#bbb', fontSize: '0.88rem', lineHeight: 1.5, margin: 0 }}>
                Se você somar as probabilidades implícitas de todos os resultados possíveis de um jogo (Casa + Empate + Fora), a soma nunca dará 100%, mas sim 104%, 106% ou mais. Essa diferença é a taxa de corretagem invisível que a casa retém de você.
              </p>
            </div>
          </section>

          {/* 2. O Maior Mito: Aposta Acima de 50% */}
          <section>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: '#1c1c24', color: 'var(--brand-neon)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center' }}>
                <ShieldAlert size={22} />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, textTransform: 'uppercase' }}>2. O Mito da Alta Probabilidade</h2>
            </div>

            <p style={{ color: '#aaa', lineHeight: 1.6, marginBottom: '20px' }}>
              O maior erro do apostador iniciante é buscar jogos em que a chance de vencer seja alta (ex: 90%). A matemática prova que a melhor aposta não é a mais provável, mas sim a que tem <strong>Valor Esperado Positivo (+EV)</strong>.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
              <div style={{ background: '#141416', border: '1px solid rgba(255, 68, 68, 0.2)', padding: '20px', borderRadius: '12px' }}>
                <h4 style={{ color: '#ff4444', fontWeight: 'bold', marginBottom: '10px', textTransform: 'uppercase', fontSize: '0.95rem' }}>❌ Exemplo de Aposta Ruim</h4>
                <p style={{ color: '#bbb', fontSize: '0.9rem', lineHeight: 1.5, margin: 0 }}>
                  Um super favorito tem 90% de chance de ganhar, mas a odd oferecida é <strong>1.05</strong>. O risco de 10% de zebra (que destrói todo o seu dinheiro) não compensa o retorno minúsculo de apenas 5 centavos por real apostado.
                </p>
              </div>

              <div style={{ background: '#141416', border: '1px solid rgba(204, 255, 0, 0.3)', padding: '20px', borderRadius: '12px' }}>
                <h4 style={{ color: 'var(--brand-neon)', fontWeight: 'bold', marginBottom: '10px', textTransform: 'uppercase', fontSize: '0.95rem' }}>✅ Exemplo de Aposta de Valor (+EV)</h4>
                <p style={{ color: '#bbb', fontSize: '0.9rem', lineHeight: 1.5, margin: 0 }}>
                  A casa de apostas oferece uma odd de <strong>3.30</strong> para um time (probabilidade implícita de 30%). No entanto, após analisar escalações e histórico, você calcula que a probabilidade real é de <strong>40%</strong>. Essa distorção é um palpite de valor (+EV).
                </p>
              </div>
            </div>
          </section>

          {/* 3. A Faixa de Odd Ideal */}
          <section>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: '#1c1c24', color: 'var(--brand-neon)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center' }}>
                <TrendingUp size={22} />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, textTransform: 'uppercase' }}>3. A Faixa de Odd Ideal (Fator Emocional)</h2>
            </div>

            <p style={{ color: '#aaa', lineHeight: 1.6, marginBottom: '20px' }}>
              Na teoria, qualquer odd desajustada tem valor. Na prática, a nossa psicologia dita qual faixa de cotação devemos buscar para não quebrar a nossa banca ou nossa disciplina emocional:
            </p>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', background: '#141416', borderRadius: '12px', overflow: 'hidden' }}>
                <thead>
                  <tr style={{ background: '#1c1c24', textTransform: 'uppercase', fontSize: '0.85rem', color: '#888' }}>
                    <th style={{ padding: '16px', textAlign: 'left' }}>Faixa de Odd</th>
                    <th style={{ padding: '16px', textAlign: 'left' }}>Classificação</th>
                    <th style={{ padding: '16px', textAlign: 'left' }}>Razão Prática & Comportamental</th>
                  </tr>
                </thead>
                <tbody style={{ fontSize: '0.9rem', color: '#ccc' }}>
                  <tr style={{ borderBottom: '1px solid #222' }}>
                    <td style={{ padding: '16px', fontWeight: 'bold', color: 'var(--brand-neon)' }}>1.60 a 2.00</td>
                    <td style={{ padding: '16px', fontWeight: 'bold' }}>⭐ Zona de Equilíbrio (Ideal)</td>
                    <td style={{ padding: '16px', color: '#aaa', lineHeight: 1.4 }}>
                      Possui taxa de acerto de ~50% ou mais. Garante constância e permite recuperar uma perda com apenas um ou dois acertos, mantendo seu psicológico estável.
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #222' }}>
                    <td style={{ padding: '16px', fontWeight: 'bold', color: '#ff9800' }}>Abaixo de 1.60</td>
                    <td style={{ padding: '16px', fontWeight: 'bold' }}>⚠️ Perigosa (Longo Prazo)</td>
                    <td style={{ padding: '16px', color: '#aaa', lineHeight: 1.4 }}>
                      Embora acerte mais, o retorno é baixo. Um único erro (red) destrói o lucro de 4 ou 5 acertos seguidos, exigindo taxas de acerto surreais para ser lucrativo no longo prazo.
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #222' }}>
                    <td style={{ padding: '16px', fontWeight: 'bold', color: '#ff4444' }}>Acima de 3.00</td>
                    <td style={{ padding: '16px', fontWeight: 'bold' }}>❌ Risco Psicológico Alto</td>
                    <td style={{ padding: '16px', color: '#aaa', lineHeight: 1.4 }}>
                      A variância é extrema. Poucos investidores têm controle emocional e banca para aguentar sequências de 10 a 20 perdas consecutivas antes de conseguir o acerto compensador.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* 4. Gestão de Banca */}
          <section>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: '#1c1c24', color: 'var(--brand-neon)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center' }}>
                <DollarSign size={22} />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, textTransform: 'uppercase' }}>4. Gestão de Banca: O Escudo Contra a Ruína</h2>
            </div>

            <p style={{ color: '#aaa', lineHeight: 1.6, marginBottom: '20px' }}>
              O método infalível para não quebrar a banca é parar de pensar no saldo em reais e passar a pensar em <strong>Unidades (U)</strong>. 
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '20px' }}>
              <div style={{ background: '#141416', border: '1px solid #222', padding: '20px', borderRadius: '12px' }}>
                <h4 style={{ fontWeight: 'bold', color: '#fff', marginBottom: '10px' }}>O Conceito de Unidades</h4>
                <p style={{ color: '#aaa', fontSize: '0.9rem', lineHeight: 1.5, margin: 0 }}>
                  Divida sua banca total em 100 partes iguais. Se você tem R$ 200,00, você possui 100 unidades de R$ 2,00. Cada aposta deve ser medida por quantas unidades (U) você irá investir.
                </p>
              </div>

              <div style={{ background: '#141416', border: '1px solid #222', padding: '20px', borderRadius: '12px' }}>
                <h4 style={{ fontWeight: 'bold', color: '#fff', marginBottom: '10px' }}>Regra de Ouro (1% a 2%)</h4>
                <p style={{ color: '#aaa', fontSize: '0.9rem', lineHeight: 1.5, margin: 0 }}>
                  A regra mais segura é nunca expor mais de <strong>1% (Conservador)</strong> ou <strong>2% (Moderado)</strong> da sua banca em um único jogo. Isso te protege de sequências ruins inevitáveis.
                </p>
              </div>

              <div style={{ background: '#141416', border: '1px solid #222', padding: '20px', borderRadius: '12px' }}>
                <h4 style={{ fontWeight: 'bold', color: '#ff4444', marginBottom: '10px' }}>Evite Apostas Múltiplas</h4>
                <p style={{ color: '#aaa', fontSize: '0.9rem', lineHeight: 1.5, margin: 0 }}>
                  A cada partida adicionada no seu bilhete de aposta, as taxas invisíveis da casa de apostas (juice) multiplicam-se de forma brutal. Múltiplas são loteria, não investimento.
                </p>
              </div>
            </div>
          </section>

          {/* 5. Proteções e Handicaps — CTA for Masterclass */}
          <section>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: '#1c1c24', color: 'var(--brand-neon)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center' }}>
                <Zap size={22} />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, textTransform: 'uppercase' }}>5. Utilizando Proteções (Handicaps Asiáticos)</h2>
            </div>

            <p style={{ color: '#aaa', lineHeight: 1.6, marginBottom: '20px' }}>
              Apostadores experientes evitam focar apenas na vitória simples de um time. Eles buscam margens de segurança através dos <strong>Handicaps Asiáticos</strong> — 
              a ferramenta matemática mais poderosa para ajustar risco e encontrar <strong style={{ color: 'var(--brand-neon)' }}>valor esperado positivo (+EV)</strong>.
            </p>

            {/* Quick preview cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: '#111118', border: '1px solid rgba(78,205,196,0.15)', borderRadius: '10px', padding: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Shield size={18} style={{ color: '#4ecdc4' }} />
                  <strong style={{ color: '#4ecdc4', fontSize: '0.85rem', textTransform: 'uppercase' }}>Linhas Positivas</strong>
                </div>
                <p style={{ color: '#888', fontSize: '0.82rem', lineHeight: 1.5, margin: 0 }}>
                  HA +0.5, +1.0, +1.5 — Proteção e segurança para a sua banca em jogos com azarões subestimados.
                </p>
              </div>
              <div style={{ background: '#111118', border: '1px solid rgba(255,107,107,0.15)', borderRadius: '10px', padding: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <Sword size={18} style={{ color: '#ff6b6b' }} />
                  <strong style={{ color: '#ff6b6b', fontSize: '0.85rem', textTransform: 'uppercase' }}>Linhas Negativas</strong>
                </div>
                <p style={{ color: '#888', fontSize: '0.82rem', lineHeight: 1.5, margin: 0 }}>
                  HA -0.5, -1.0 — Martelos de valor para favoritos que vencem com autoridade e odds esmagadas.
                </p>
              </div>
              <div style={{ background: '#111118', border: '1px solid rgba(255,217,61,0.15)', borderRadius: '10px', padding: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <AlertTriangle size={18} style={{ color: '#ffd93d' }} />
                  <strong style={{ color: '#ffd93d', fontSize: '0.85rem', textTransform: 'uppercase' }}>Linhas de Quarto</strong>
                </div>
                <p style={{ color: '#888', fontSize: '0.82rem', lineHeight: 1.5, margin: 0 }}>
                  ±0.25, ±0.75 — O sistema divide a aposta em duas partes iguais para pulverizar o risco.
                </p>
              </div>
            </div>

            {/* CTA to Masterclass */}
            <Link href="/tutorial/handicap" style={{ textDecoration: 'none' }}>
              <div style={{
                background: 'linear-gradient(135deg, rgba(204,255,0,0.04), rgba(78,205,196,0.04))',
                border: '1px solid rgba(204,255,0,0.25)',
                borderRadius: '16px',
                padding: '24px 28px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '16px',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--brand-neon)', textTransform: 'uppercase', letterSpacing: '2px' }}>
                      Masterclass Avançada
                    </span>
                  </div>
                  <h3 style={{ fontWeight: 800, fontSize: '1.2rem', color: '#fff', margin: 0, marginBottom: '6px' }}>
                    Dominando o Handicap Asiático — Guia Completo
                  </h3>
                  <p style={{ color: '#888', fontSize: '0.85rem', margin: 0, lineHeight: 1.5 }}>
                    5 módulos completos com conceito matemático, linhas defensivas e agressivas, linhas de quarto e integração com gestão de unidades.
                  </p>
                </div>
                <ArrowRight size={28} style={{ color: 'var(--brand-neon)', flexShrink: 0 }} />
              </div>
            </Link>
          </section>

          {/* 6. Planilha de Registros e Fórmulas Matemáticas (+EV) */}
          <section>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: '#1c1c24', color: 'var(--brand-neon)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center' }}>
                <CheckCircle2 size={22} />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, textTransform: 'uppercase' }}>6. Planilha de Registros e Fórmula +EV</h2>
            </div>

            <p style={{ color: '#aaa', lineHeight: 1.6, marginBottom: '20px' }}>
              Registrar suas apostas de forma analítica é o único caminho para entender se suas técnicas de precificação possuem <strong>vantagem real sobre as casas de apostas</strong>.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
              <div style={{ background: '#141416', border: '1px solid #222', padding: '20px', borderRadius: '12px' }}>
                <h4 style={{ color: '#fff', fontWeight: 'bold', marginBottom: '12px', fontSize: '1rem' }}>A Fórmula Matemática de EV</h4>
                <p style={{ color: '#bbb', fontSize: '0.88rem', lineHeight: 1.5, marginBottom: '14px' }}>
                  A vantagem matemática é obtida quando multiplicamos a probabilidade real pela odd e removemos a unidade apostada. Multiplicamos por 100 para visualizar a taxa de valor em porcentagem:
                </p>
                <div style={{ background: '#0a0a0f', border: '1px solid #222', borderRadius: '8px', padding: '12px', fontFamily: 'monospace', color: 'var(--brand-neon)', textAlign: 'center', fontWeight: 'bold', fontSize: '1rem' }}>
                  =((Probabilidade / 100) * Odd - 1) * 100
                </div>
              </div>

              <div style={{ background: '#141416', border: '1px solid #222', padding: '20px', borderRadius: '12px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <h4 style={{ color: '#fff', fontWeight: 'bold', marginBottom: '12px', fontSize: '1rem' }}>Modelo Pronto Gratuito</h4>
                  <p style={{ color: '#bbb', fontSize: '0.88rem', lineHeight: 1.5, margin: 0 }}>
                    Disponibilizamos um modelo oficial e estilizado da planilha com o cabeçalho colorido da <strong>A2 Sports Tracker</strong> e as fórmulas dinâmicas de EV prontas para uso no Excel ou Google Sheets. Baixe gratuitamente agora!
                  </p>
                </div>
                <button
                  type="button"
                  onClick={downloadExcelTemplate}
                  style={{
                    background: 'var(--brand-neon)',
                    color: '#000',
                    border: 'none',
                    padding: '10px 18px',
                    borderRadius: '8px',
                    fontWeight: 'bold',
                    fontSize: '0.82rem',
                    cursor: 'pointer',
                    marginTop: '14px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    boxShadow: '0 4px 15px rgba(204, 255, 0, 0.2)',
                    transition: 'all 0.2s'
                  }}
                >
                  📥 Baixar Planilha Modelo (+EV)
                </button>
              </div>
            </div>
          </section>

          {/* 7. Como nosso sistema ajuda você? */}
          <section style={{ borderTop: '1px solid #1f1f2e', paddingTop: '40px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <div style={{ background: '#1c1c24', color: 'var(--brand-neon)', padding: '10px', borderRadius: '12px', display: 'flex', alignItems: 'center' }}>
                <Award size={22} />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, textTransform: 'uppercase' }}>7. Como nos destacamos e ajudamos você</h2>
            </div>

            <p style={{ color: '#aaa', lineHeight: 1.6, marginBottom: '24px' }}>
              Nosso sistema trabalha 24 horas por dia rodando simulações matemáticas para te entregar as melhores cotações sem que você precise fazer contas complexas manualmente:
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
              <div style={{ background: '#141419', border: '1px solid #222', borderRadius: '12px', padding: '20px' }}>
                <span style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--brand-neon)' }}>01</span>
                <h4 style={{ fontWeight: 'bold', color: '#fff', marginTop: '12px', marginBottom: '8px' }}>Monitoramento de Ligas em Tempo Real</h4>
                <p style={{ color: '#888', fontSize: '0.85rem', lineHeight: 1.5, margin: 0 }}>
                  Acompanhamos as partidas das principais ligas e calculamos odds reais por Poisson para cruzar com as cotações oferecidas nas maiores casas de apostas.
                </p>
              </div>

              <div style={{ background: '#141419', border: '1px solid #222', borderRadius: '12px', padding: '20px' }}>
                <span style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--brand-neon)' }}>02</span>
                <h4 style={{ fontWeight: 'bold', color: '#fff', marginTop: '12px', marginBottom: '8px' }}>Fórmula de Kelly Personalizada</h4>
                <p style={{ color: '#888', fontSize: '0.85rem', lineHeight: 1.5, margin: 0 }}>
                  Com base no tamanho da sua banca configurada no painel, nossos alertas no Telegram calculam de forma dinâmica a porcentagem ideal de investimento (stake) para cada dica.
                </p>
              </div>

              <div style={{ background: '#141419', border: '1px solid #222', borderRadius: '12px', padding: '20px' }}>
                <span style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--brand-neon)' }}>03</span>
                <h4 style={{ fontWeight: 'bold', color: '#fff', marginTop: '12px', marginBottom: '8px' }}>Histórico 100% Transparente</h4>
                <p style={{ color: '#888', fontSize: '0.85rem', lineHeight: 1.5, margin: 0 }}>
                  Todas as oportunidades geradas são confrontadas automaticamente contra placares reais. Você acompanha ROI, taxa de acerto e resultados passados de forma transparente no painel.
                </p>
              </div>
            </div>
          </section>

          {/* Quick Summary list */}
          <div style={{
            background: '#141416',
            border: '1px solid #222',
            borderRadius: '16px',
            padding: '28px',
            marginTop: '20px'
          }}>
            <h3 style={{ fontWeight: 'bold', fontSize: '1.2rem', color: '#fff', marginBottom: '16px', textTransform: 'uppercase' }}>📝 Checklist Rápido de Proteção:</h3>
            <ul style={{ color: '#aaa', fontSize: '0.95rem', lineHeight: 1.8, paddingLeft: '20px', margin: 0 }}>
              <li><strong>Pare de adivinhar resultados:</strong> Busque apenas odds com desajuste de valor (+EV).</li>
              <li><strong>Opere na zona ideal:</strong> Dê preferência a odds entre 1.60 e 2.00 para conter a variância.</li>
              <li><strong>Proteja sua banca:</strong> Nunca aposte mais que 1% a 2% do seu saldo total por jogo.</li>
              <li><strong>Anote tudo:</strong> Use nossa Central e a aba Carteira para catalogar seus resultados e acompanhar seus ganhos.</li>
            </ul>
          </div>

        </div>
    </div>
  );
}
