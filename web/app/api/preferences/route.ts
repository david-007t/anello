import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { supabaseAdmin } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = await req.json();

  const { error } = await supabaseAdmin()
    .from("preferences")
    .upsert({ user_id: userId, ...body, updated_at: new Date().toISOString() }, { onConflict: 'user_id' });

  if (error) {
    console.error("[preferences POST] Supabase error:", JSON.stringify(error));
    return NextResponse.json({ error: "Could not save preferences" }, { status: 500 });
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
