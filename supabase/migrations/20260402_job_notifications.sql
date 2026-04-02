create table if not exists job_notifications (
  id uuid default gen_random_uuid() primary key,
  user_id uuid not null,
  job_url text not null,
  job_title text,
  company text,
  notified_at timestamptz default now(),
  unique(user_id, job_url)
);
