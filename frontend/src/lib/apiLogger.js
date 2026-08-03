import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
const supabaseServiceRole = process.env.SUPABASE_SERVICE_ROLE_KEY || '';

const supabaseAdmin = createClient(supabaseUrl, supabaseServiceRole, {
  auth: { autoRefreshToken: false, persistSession: false }
});

export async function logApiCall(endpoint, remainingQuota = -1, blocked = false) {
  try {
    const { error } = await supabaseAdmin
      .from('api_usage_log')
      .insert({
        endpoint,
        remaining_quota: remainingQuota,
        blocked,
        called_at: new Date().toISOString()
      });
    if (error) {
      console.error('[API Logger] Error inserting usage log:', error);
    }
  } catch (err) {
    console.error('[API Logger] Error logging call:', err);
  }
}
