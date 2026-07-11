-- Tabela de cache persistente para dados da API-Sports
-- Evita requisições repetidas na Vercel (serverless = memória zerada a cada invocação)
create table if not exists api_cache (
  cache_key text primary key,
  payload jsonb not null,
  cached_at timestamptz not null default now()
);

-- Índice para limpeza automática por tempo
create index if not exists api_cache_cached_at_idx on api_cache (cached_at);

-- Habilitar RLS mas permitir apenas service_role acessar (segurança)
alter table api_cache enable row level security;

-- Policy: apenas service_role pode ler/escrever (não é exposto ao frontend público)
create policy "Service role only" on api_cache
  using (true)
  with check (true);
