import { NextResponse } from 'next/server';

// Rate limiter simplificado em memória utilizando as APIs nativas Edge do Next.js
const rateLimitMap = new Map();

// Limpar o cache de IPs a cada 1 minuto para economizar memória e resetar o limite
setInterval(() => {
  rateLimitMap.clear();
}, 60 * 1000);

export function middleware(request) {
  // Aplicar Rate Limiting apenas nas rotas de API
  if (request.nextUrl.pathname.startsWith('/api/')) {
    // Obter o IP do cliente através dos cabeçalhos da Vercel/Cloudflare ou padrão
    const ip = request.headers.get('x-forwarded-for') || '127.0.0.1';
    
    const limit = 100; // Máximo de 100 requisições por minuto por IP
    const currentUsage = rateLimitMap.get(ip) || 0;

    if (currentUsage >= limit) {
      console.warn(`[Rate Limit] IP ${ip} bloqueado temporariamente por excesso de requisições.`);
      return new NextResponse(
        JSON.stringify({ error: 'Muitas requisições. Por favor, tente novamente em um minuto.' }),
        {
          status: 429,
          headers: {
            'Content-Type': 'application/json',
            'Retry-After': '60'
          }
        }
      );
    }

    rateLimitMap.set(ip, currentUsage + 1);
  }

  return NextResponse.next();
}

// Configurar o middleware para interceptar apenas as rotas sob /api/:path*
export const config = {
  matcher: '/api/:path*'
};
