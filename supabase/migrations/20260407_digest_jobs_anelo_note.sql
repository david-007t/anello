-- Add anelo_note column to digest_jobs so AI-generated recommendations
-- are persisted alongside each job and available across pipeline runs.
alter table digest_jobs add column if not exists anelo_note text default '';
