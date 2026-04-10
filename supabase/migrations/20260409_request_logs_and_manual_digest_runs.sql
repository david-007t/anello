create table if not exists request_logs (
  id uuid default gen_random_uuid() primary key,
  action text not null,
  user_id text,
  email text,
  ip text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create index if not exists request_logs_action_created_at_idx
  on request_logs(action, created_at desc);

create index if not exists request_logs_action_user_id_created_at_idx
  on request_logs(action, user_id, created_at desc);

create index if not exists request_logs_action_ip_created_at_idx
  on request_logs(action, ip, created_at desc);

create index if not exists request_logs_action_email_created_at_idx
  on request_logs(action, email, created_at desc);
