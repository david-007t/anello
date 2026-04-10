import { supabaseAdmin } from "@/lib/supabase";

interface CountRecentOptions {
  action: string;
  sinceIso: string;
  userId?: string;
  ip?: string;
  email?: string;
}

interface LogRequestOptions {
  action: string;
  userId?: string;
  ip?: string;
  email?: string;
  metadata?: Record<string, unknown>;
}

export async function countRecentRequests({
  action,
  sinceIso,
  userId,
  ip,
  email,
}: CountRecentOptions): Promise<number> {
  let query = supabaseAdmin()
    .from("request_logs")
    .select("*", { count: "exact", head: true })
    .eq("action", action)
    .gte("created_at", sinceIso);

  if (userId) query = query.eq("user_id", userId);
  if (ip) query = query.eq("ip", ip);
  if (email) query = query.eq("email", email);

  const { count, error } = await query;
  if (error) {
    throw new Error(error.message);
  }

  return count ?? 0;
}

export async function logRequest({
  action,
  userId,
  ip,
  email,
  metadata = {},
}: LogRequestOptions): Promise<void> {
  const { error } = await supabaseAdmin().from("request_logs").insert({
    action,
    user_id: userId ?? null,
    ip: ip ?? null,
    email: email ?? null,
    metadata,
  });

  if (error) {
    throw new Error(error.message);
  }
}
