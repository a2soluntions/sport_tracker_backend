import { NextResponse } from 'next/server';
import { getPayment } from '@/lib/mercadopago';
import { createClient } from '@supabase/supabase-js';

export const dynamic = 'force-dynamic';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

function getAdminSupabase() {
  if (!supabaseUrl || !supabaseServiceKey) return null;
  return createClient(supabaseUrl, supabaseServiceKey, {
    auth: { autoRefreshToken: false, persistSession: false }
  });
}

export async function GET(request) {
  try {
    const authHeader = request.headers.get('Authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Acesso não autorizado.' }, { status: 401 });
    }
    const token = authHeader.split(' ')[1];
    const supabase = getAdminSupabase();
    if (!supabase) {
      return NextResponse.json({ error: 'Erro de configuração do servidor.' }, { status: 500 });
    }
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);
    if (authError || !user) {
      return NextResponse.json({ error: 'Usuário não autenticado.' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const paymentId = searchParams.get('id');

    if (!paymentId) {
      return NextResponse.json({ error: 'ID do pagamento é obrigatório.' }, { status: 400 });
    }

    const payment = await getPayment(paymentId);
    const status = payment.status;
    const externalReference = payment.external_reference;

    // SEC-3: Validar se o usuário que consulta é o dono do pagamento ou um admin
    let isOwner = false;
    let isAdmin = user.email === 'a2soluntions@gmail.com';

    if (externalReference && externalReference.includes(':')) {
      const [paymentUserId] = externalReference.split(':');
      if (paymentUserId === user.id) {
        isOwner = true;
      }
    }

    if (!isOwner && !isAdmin) {
      const { data: profile } = await supabase
        .from('profiles')
        .select('role')
        .eq('id', user.id)
        .maybeSingle();

      if (profile?.role === 'admin' || profile?.role === 'super_admin') {
        isAdmin = true;
      }
    }

    if (!isOwner && !isAdmin) {
      return NextResponse.json({ error: 'Acesso negado a este pagamento.' }, { status: 403 });
    }

    // Se o pagamento estiver aprovado, garantir que o plano está ativado no banco de dados
    if (status === 'approved') {
      const externalReference = payment.external_reference;
      if (externalReference && externalReference.includes(':')) {
        const [userId, planKey, couponCode] = externalReference.split(':');
        
        const supabase = getAdminSupabase();
        if (supabase && userId && planKey) {
          const { error } = await supabase
            .from('profiles')
            .update({
              plan: planKey,
              coupon_code: couponCode || null
            })
            .eq('id', userId);

          if (error) {
            console.error('[Status API] Erro ao atualizar perfil no Supabase:', error);
          } else {
            console.log(`[Status API] Sucesso: Plano ${planKey} ativado para o usuário ${userId}`);
          }
        }
      }
    }

    return NextResponse.json({ status });

  } catch (err) {
    console.error('[Status API Error]:', err);
    return NextResponse.json({ error: err.message || 'Erro ao consultar status.' }, { status: 500 });
  }
}
