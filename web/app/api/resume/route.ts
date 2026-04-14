import { NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { supabaseAdmin } from "@/lib/supabase";

export async function GET() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { data, error } = await supabaseAdmin()
    .from("resumes")
    .select("file_name, file_path, uploaded_at")
    .eq("user_id", userId)
    .order("uploaded_at", { ascending: false })
    .limit(1)
    .single();

  if (error && error.code !== "PGRST116") {
    console.error("[resume GET] Supabase error:", error);
    return NextResponse.json({ error: "Could not load resume" }, { status: 500 });
  }

  return NextResponse.json({ data: data || null });
}
