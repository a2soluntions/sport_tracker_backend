-- ============================================================
-- Tabela de log de uso da API-Sports
-- Criada pelo api_guard.py (backend Python) para rastrear
-- todas as chamadas feitas à API, com saldo restante e status.
-- ============================================================
create table if not exists api_usage_log (
  id          bigserial primary key,
  endpoint    text        not null,
  remaining_quota integer default -1,  -- saldo retornado pelo header x-ratelimit-requests-remaining
  blocked     boolean     not null default false, -- true = chamada bloqueada pelo guard
  called_at   timestamptz not null default now()
);

-- Índice para consultas por data (usado no budget guard)
create index if not exists api_usage_log_called_at_idx on api_usage_log (called_at);
create index if not exists api_usage_log_blocked_idx   on api_usage_log (blocked);

-- RLS: somente service_role pode escrever/ler
alter table api_usage_log enable row level security;

-- Limpeza automática: remove registros com mais de 7 dias
-- (execute manualmente ou configure um cron no Supabase)
-- delete from api_usage_log where called_at < now() - interval '7 days';

-- View útil: consumo de hoje por hora
create or replace view api_usage_hoje as
select
  date_trunc('hour', called_at at time zone 'America/Sao_Paulo') as hora,
  count(*) filter (where not blocked) as chamadas_realizadas,
  count(*) filter (where blocked)     as chamadas_bloqueadas,
  min(remaining_quota) filter (where remaining_quota >= 0) as saldo_minimo
from api_usage_log
where called_at >= current_date
group by 1
order by 1;
