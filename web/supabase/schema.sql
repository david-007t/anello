-- Anelo Database Schema
-- Run this in Supabase SQL Editor: Project → SQL Editor → New Query → paste + run

-- Users (synced from Clerk via webhook)
create table if not exists users (
  id text primary key,
  email text not null,
  first_name text,
  last_name text,
  created_at timestamptz default now()
);

-- Resumes
create table if not exists resumes (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  file_path text not null,
  file_name text not null,
  uploaded_at timestamptz default now()
);

-- Job preferences
create table if not exists preferences (
  id uuid primary key default gen_random_uuid(),
  user_id text not null unique,
  role text,
  location text,
  min_salary text,
  company_types text,
  skills text,
  updated_at timestamptz default now()
);

-- Applications
create table if not exists applications (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  company text not null,
  role text not null,
  job_url text,
  ats text,
  resume_version text,
  status text default 'applied',
  applied_at timestamptz default now(),
  notes text
);

-- Job digest items
create table if not exists digest_jobs (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  company text not null,
  role text not null,
  job_url text,
  location text,
  salary_range text,
  source text,
  matched_at timestamptz default now(),
  applied boolean default false
);

-- Waitlist (backup — also captured via Resend)
create table if not exists waitlist (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  created_at timestamptz default now()
);

-- RLS: users can only read/write their own data
alter table resumes enable row level security;
alter table preferences enable row level security;
alter table applications enable row level security;
alter table digest_jobs enable row level security;

-- Storage bucket for resumes
insert into storage.buckets (id, name, public)
values ('resumes', 'resumes', false)
on conflict do nothing;
