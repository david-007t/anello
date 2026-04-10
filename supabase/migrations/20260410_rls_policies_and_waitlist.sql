begin;

alter table if exists public.users enable row level security;
alter table if exists public.preferences enable row level security;
alter table if exists public.resumes enable row level security;
alter table if exists public.applications enable row level security;
alter table if exists public.digest_jobs enable row level security;
alter table if exists public.request_logs enable row level security;

create table if not exists public.waitlist (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  created_at timestamptz not null default now()
);

alter table public.waitlist enable row level security;

drop policy if exists "Users read own profile row" on public.users;
create policy "Users read own profile row"
on public.users
for select
to authenticated
using (id = (auth.uid())::text);

drop policy if exists "Users read own preferences" on public.preferences;
create policy "Users read own preferences"
on public.preferences
for select
to authenticated
using (user_id = (auth.uid())::text);

drop policy if exists "Users insert own preferences" on public.preferences;
create policy "Users insert own preferences"
on public.preferences
for insert
to authenticated
with check (user_id = (auth.uid())::text);

drop policy if exists "Users update own preferences" on public.preferences;
create policy "Users update own preferences"
on public.preferences
for update
to authenticated
using (user_id = (auth.uid())::text)
with check (user_id = (auth.uid())::text);

drop policy if exists "Users delete own preferences" on public.preferences;
create policy "Users delete own preferences"
on public.preferences
for delete
to authenticated
using (user_id = (auth.uid())::text);

drop policy if exists "Users read own resumes" on public.resumes;
create policy "Users read own resumes"
on public.resumes
for select
to authenticated
using (user_id = (auth.uid())::text);

drop policy if exists "Users insert own resumes" on public.resumes;
create policy "Users insert own resumes"
on public.resumes
for insert
to authenticated
with check (user_id = (auth.uid())::text);

drop policy if exists "Users update own resumes" on public.resumes;
create policy "Users update own resumes"
on public.resumes
for update
to authenticated
using (user_id = (auth.uid())::text)
with check (user_id = (auth.uid())::text);

drop policy if exists "Users delete own resumes" on public.resumes;
create policy "Users delete own resumes"
on public.resumes
for delete
to authenticated
using (user_id = (auth.uid())::text);

drop policy if exists "Users read own applications" on public.applications;
create policy "Users read own applications"
on public.applications
for select
to authenticated
using (user_id = (auth.uid())::text);

drop policy if exists "Users insert own applications" on public.applications;
create policy "Users insert own applications"
on public.applications
for insert
to authenticated
with check (user_id = (auth.uid())::text);

drop policy if exists "Users update own applications" on public.applications;
create policy "Users update own applications"
on public.applications
for update
to authenticated
using (user_id = (auth.uid())::text)
with check (user_id = (auth.uid())::text);

drop policy if exists "Users delete own applications" on public.applications;
create policy "Users delete own applications"
on public.applications
for delete
to authenticated
using (user_id = (auth.uid())::text);

drop policy if exists "Users see own digest jobs" on public.digest_jobs;
create policy "Users see own digest jobs"
on public.digest_jobs
for select
to authenticated
using (user_id = (auth.uid())::text);

drop policy if exists "Users read own resume objects" on storage.objects;
create policy "Users read own resume objects"
on storage.objects
for select
to authenticated
using (
  bucket_id = 'resumes'
  and (storage.foldername(name))[1] = (auth.uid())::text
);

drop policy if exists "Users insert own resume objects" on storage.objects;
create policy "Users insert own resume objects"
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'resumes'
  and (storage.foldername(name))[1] = (auth.uid())::text
);

drop policy if exists "Users update own resume objects" on storage.objects;
create policy "Users update own resume objects"
on storage.objects
for update
to authenticated
using (
  bucket_id = 'resumes'
  and (storage.foldername(name))[1] = (auth.uid())::text
)
with check (
  bucket_id = 'resumes'
  and (storage.foldername(name))[1] = (auth.uid())::text
);

drop policy if exists "Users delete own resume objects" on storage.objects;
create policy "Users delete own resume objects"
on storage.objects
for delete
to authenticated
using (
  bucket_id = 'resumes'
  and (storage.foldername(name))[1] = (auth.uid())::text
);

commit;
