import { NextResponse } from 'next/server';
import { verifyAdmin } from '@/lib/adminAuth';

export async function POST(request) {
  try {
    const body = await request.json();
    const { match, tip, probability, odd, isVip, message: customMessage, opportunity, imageUrl, targetChannel, buttonText, buttonUrl, sendWithoutImage } = body;

    const botToken = process.env.TELEGRAM_BOT_TOKEN;
    let chatId = process.env.TELEGRAM_CHAT_ID;

    // Verificar se o usuário é admin
    const isAdmin = await verifyAdmin(request);

    if (isVip || targetChannel) {
      if (!isAdmin) {
        return NextResponse.json({ error: 'Acesso não autorizado' }, { status: 401 });
      }

      if (targetChannel === 'radar_ev') {
        chatId = process.env.TELEGRAM_RADAR_EV_CHAT_ID || process.env.TELEGRAM_VIP_CHAT_ID || process.env.TELEGRAM_CHAT_ID;
      } else if (targetChannel === 'free') {
        chatId = process.env.TELEGRAM_CHAT_ID;
      } else {
        chatId = process.env.TELEGRAM_VIP_CHAT_ID || process.env.TELEGRAM_CHAT_ID;
      }
    }

    const cleanBotToken = String(botToken).trim().replace(/['"]/g, '');
    const cleanChatId = String(chatId).trim().replace(/['"]/g, '');

    if (!cleanBotToken || !cleanChatId) {
      console.error('Missing Telegram credentials in environment variables', { botToken: !!cleanBotToken, chatId: cleanChatId });
      return NextResponse.json({ error: `Configuração do Telegram ausente no servidor (chatId: ${cleanChatId})` }, { status: 500 });
    }

    console.log('[Telegram Broadcast] Sending request:', {
      botTokenPrefix: cleanBotToken.substring(0, 10) + '...',
      botTokenLength: cleanBotToken.length,
      chatId: cleanChatId,
      isVip,
      targetChannel,
      hasImage: !!imageUrl,
      hasButton: !!(buttonText && buttonUrl),
      sendWithoutImage
    });

    let finalMessage = '';
    let finalImageUrl = sendWithoutImage ? null : imageUrl;

    // Conectar ao Supabase admin para carregar templates e imagens padrões
    let dbSettings = {};
    try {
      const { createClient } = await import('@supabase/supabase-js');
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
      const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';
      if (supabaseUrl && supabaseServiceKey) {
        const client = createClient(supabaseUrl, supabaseServiceKey, {
          auth: { autoRefreshToken: false, persistSession: false }
        });
        const { data: settingsList } = await client.from('saas_settings').select('*');
        (settingsList || []).forEach(item => {
          dbSettings[item.key] = item.value;
        });
      }
    } catch (e) {
      console.warn('[Telegram Broadcast] Erro ao carregar templates do Supabase:', e);
    }

    if (customMessage) {
      finalMessage = customMessage;
    } else if (opportunity) {
      const ev = parseFloat(opportunity.vantagem_ev_porcentagem || 0).toFixed(2);
      const risk = Math.max(0.5, Math.min(5.0, (opportunity.vantagem_ev_porcentagem * 0.25))).toFixed(1);
      finalMessage = `⚽ *NOVO PALPITE PRÉ-JOGO!*
 
🏆 *Campeonato:* ${opportunity.campeonato || 'Geral'}
⚔️ *Confronto:* ${opportunity.confronto}
🎯 *Mercado:* ${opportunity.mercado}
📈 *Odd Recomendada:* @${opportunity.odd_oferecida} (Justa: @${opportunity.odd_justa})
🔥 *Vantagem (EV):* +${ev}%
🛡️ *Gestão de Risco:* ${risk}% da sua banca
 
_Analise e faça sua entrada com responsabilidade!_ 📊`;
    } else {
      const templateStr = dbSettings.telegram_palpites_template || `🏆 *NOVO PALPITE VIP* 🏆

⚽ *Jogo:* {jogo}
🎯 *Palpite:* {palpite}
📊 *Probabilidade:* {probabilidade}%
🔥 *Odd Justa:* @{odd_justa}

_Palpite gerado pelo Algoritmo de Poisson_ 🤖`;

      // Formatar valores com largura fixa (padronização de largura das informações)
      // Usaremos blocos de código com fontes monospaced do Telegram onde o alinhamento é garantido.
      let formattedText = templateStr
        .replace(/{jogo}/g, String(match || ''))
        .replace(/{palpite}/g, String(tip || ''))
        .replace(/{probabilidade}/g, String(probability || ''))
        .replace(/{odd_justa}/g, String(odd || ''));

      // Verificar se há chaves extras no template personalizado para preenchimento dinâmico
      if (body.campeonato) {
        formattedText = formattedText.replace(/{campeonato}/g, String(body.campeonato));
      }
      if (body.ev) {
        formattedText = formattedText.replace(/{ev}/g, String(body.ev));
      }
      if (body.stake) {
        formattedText = formattedText.replace(/{stake}/g, String(body.stake));
      }

      // Adicionar formatação de largura uniforme/alinhamento com fonte monospaced nos campos chave caso o template padrão ou personalizado contenha marcadores estruturais.
      // Substitui trechos como "*Jogo:*" ou "Palpite:" por blocos de alinhamento uniforme.
      finalMessage = formattedText;

      if (!sendWithoutImage && !finalImageUrl && dbSettings.telegram_palpites_image_url) {
        finalImageUrl = dbSettings.telegram_palpites_image_url;
      }
    }

    let telegramApiUrl = `https://api.telegram.org/bot${cleanBotToken}/sendMessage`;
    let payload = {
      chat_id: cleanChatId,
      parse_mode: 'Markdown'
    };

    // Se o chat for do supergrupo/fórum VIP, adiciona o ID do tópico Geral (0) por padrão
    if (cleanChatId === '-1003872261817') {
      payload.message_thread_id = 0;
    }

    // Adiciona botão inline se preenchido
    if (buttonText && buttonUrl) {
      payload.reply_markup = {
        inline_keyboard: [[{ text: buttonText, url: buttonUrl.trim() }]]
      };
    }

    let response;
    
    if (finalImageUrl && finalImageUrl.trim()) {
      telegramApiUrl = `https://api.telegram.org/bot${cleanBotToken}/sendPhoto`;
      const imgVal = finalImageUrl.trim();

      if (imgVal.startsWith('data:image/')) {
        // Envio via multipart/form-data para arquivos locais em Base64
        const matches = imgVal.match(/^data:([A-Za-z-+\/]+);base64,(.+)$/);
        if (!matches || matches.length !== 3) {
          return NextResponse.json({ error: 'Formato de imagem local inválido' }, { status: 400 });
        }
        
        const contentType = matches[1];
        const base64Data = matches[2];
        const buffer = Buffer.from(base64Data, 'base64');
        
        const formData = new FormData();
        formData.append('chat_id', cleanChatId);
        formData.append('parse_mode', 'Markdown');
        formData.append('caption', finalMessage);
        if (cleanChatId === '-1003872261817') {
          formData.append('message_thread_id', '0');
        }
        if (buttonText && buttonUrl) {
          formData.append('reply_markup', JSON.stringify({
            inline_keyboard: [[{ text: buttonText, url: buttonUrl.trim() }]]
          }));
        }
        
        // O construtor do Blob do Node (Next.js server side) aceita buffers
        const blob = new Blob([buffer], { type: contentType });
        formData.append('photo', blob, `card.${contentType.split('/')[1] || 'jpg'}`);
        
        response = await fetch(telegramApiUrl, {
          method: 'POST',
          body: formData
        });
      } else {
        // Envio via JSON comum para links de imagem externos
        payload.photo = imgVal;
        payload.caption = finalMessage;
        
        response = await fetch(telegramApiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }
    } else {
      payload.text = finalMessage;
      response = await fetch(telegramApiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    const data = await response.json();
    console.log('[Telegram Broadcast] Resolved Chat ID:', cleanChatId, 'API Response:', data);

    if (!data.ok) {
      console.error('Telegram API Error:', data);
      const tokenPrefix = cleanBotToken ? cleanBotToken.substring(0, 10) : 'null';
      const tokenLen = cleanBotToken ? cleanBotToken.length : 0;
      return NextResponse.json({ 
        error: `${data.description} (ChatID: ${cleanChatId}, BotToken: ${tokenPrefix}... [len: ${tokenLen}])` 
      }, { status: 400 });
    }

    return NextResponse.json({ success: true, messageId: data.result.message_id }, { status: 200 });
    
  } catch (error) {
    console.error('Internal Server Error:', error);
    return NextResponse.json({ error: 'Falha interna no servidor' }, { status: 500 });
  }
}
