alter table public.daily_log enable row level security;
alter table public.redeem_log enable row level security;
alter table public.weekly_log enable row level security;

revoke all on table public.daily_log from public;
revoke all on table public.redeem_log from public;
revoke all on table public.weekly_log from public;

revoke all on table public.daily_log from anon, authenticated;
revoke all on table public.redeem_log from anon, authenticated;
revoke all on table public.weekly_log from anon, authenticated;

select schemaname, tablename, rowsecurity
from pg_tables
where schemaname = 'public'
  and tablename in ('daily_log', 'redeem_log', 'weekly_log')
order by tablename;
