import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";
import { enforceSameOrigin } from "@/lib/api-security";
import { supabaseAdmin } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const originError = enforceSameOrigin(req);
  if (originError) return originError;

  const { error } = await supabaseAdmin()
    .from("digest_jobs")
    .delete()
    .eq("user_id", userId);

  if (error) {
    console.error("[clear-digest] Supabase error:", error);
    return NextResponse.json({ error: "Could not clear digest" }, { status: 500 });
  }
  return NextResponse.json({ status: "cleared" });
}
