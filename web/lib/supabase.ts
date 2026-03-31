import { createClient } from "@supabase/supabase-js";

function getClient(key: string) {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const secret = process.env[key];
  if (!url || !secret) throw new Error(`Missing Supabase env: NEXT_PUBLIC_SUPABASE_URL / ${key}`);
  return createClient(url, secret);
}

// Call these inside request handlers, not at module level
export const supabase = () => getClient("NEXT_PUBLIC_SUPABASE_ANON_KEY");
export const supabaseAdmin = () => getClient("SUPABASE_SERVICE_ROLE_KEY");
