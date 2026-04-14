import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { enforceSameOrigin, getClientIp, sanitizeText } from "@/lib/api-security";
import { countRecentRequests, logRequest } from "@/lib/request-limits";
import { supabaseAdmin } from "@/lib/supabase";

const PREFERENCE_LIMIT_WINDOW_MS = 10 * 60 * 1000;
const PREFERENCE_LIMIT_MAX = 30;

const ALLOWED_FIELDS = {
  role: 120,
  role_2: 120,
  role_3: 120,
  location: 120,
  min_salary: 40,
  company_types: 200,
  skills: 300,
  current_role_title: 120,
  years_experience: 40,
  key_skills: 300,
  current_salary: 40,
  current_location: 120,
  experience_min: 40,
  experience_max: 40,
  work_arrangement: 40,
  desired_locations: 160,
  work_life_balance: 200,
  industry_domain: 160,
  values_impact: 200,
} as const;

function sanitizePreferences(body: unknown): Record<string, string> {
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return {};
  }

  const sanitized: Record<string, string> = {};

  for (const [key, maxLength] of Object.entries(ALLOWED_FIELDS)) {
    const value = sanitizeText((body as Record<string, unknown>)[key], maxLength);
    if (value !== undefined) {
      sanitized[key] = value;
    }
  }

  return sanitized;
}

export async function POST(req: NextRequest) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const originError = enforceSameOrigin(req);
  if (originError) return originError;

  const ip = getClientIp(req);

  try {
    const sinceIso = new Date(Date.now() - PREFERENCE_LIMIT_WINDOW_MS).toISOString();
    const [userCount, ipCount] = await Promise.all([
      countRecentRequests({ action: "preferences_write", userId, sinceIso }),
      countRecentRequests({ action: "preferences_write", ip, sinceIso }),
    ]);

    if (userCount >= PREFERENCE_LIMIT_MAX || ipCount >= PREFERENCE_LIMIT_MAX) {
      return NextResponse.json({ error: "Too many updates. Please try again shortly." }, { status: 429 });
    }
  } catch (error) {
    console.error("[preferences POST] rate limit check failed:", error);
  }

  const body = sanitizePreferences(await req.json());

  const { error } = await supabaseAdmin()
    .from("preferences")
    .upsert({ user_id: userId, ...body, updated_at: new Date().toISOString() }, { onConflict: 'user_id' });

  if (error) {
    console.error("[preferences POST] Supabase error:", JSON.stringify(error));
    return NextResponse.json({ error: "Could not save preferences" }, { status: 500 });
  }

  try {
    await logRequest({ action: "preferences_write", userId, ip, metadata: { fields: Object.keys(body) } });
  } catch (error) {
    console.error("[preferences POST] request log failed:", error);
  }

  return NextResponse.json({ ok: true });
}

export async function GET() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { data, error } = await supabaseAdmin()
    .from("preferences")
    .select("*")
    .eq("user_id", userId)
    .single();

  if (error && error.code !== "PGRST116") {
    console.error("[preferences GET] Supabase error:", JSON.stringify(error));
    return NextResponse.json({ error: "Could not load preferences" }, { status: 500 });
  }

  return NextResponse.json({ data: data || null });
}
