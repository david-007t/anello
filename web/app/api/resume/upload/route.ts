import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { enforceSameOrigin } from "@/lib/api-security";
import { supabaseAdmin } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const originError = enforceSameOrigin(req);
  if (originError) return originError;

  const form = await req.formData();
  const file = form.get("resume") as File | null;

  if (!file) return NextResponse.json({ error: "No file provided" }, { status: 400 });

  const allowed = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
  if (!allowed.includes(file.type)) {
    return NextResponse.json({ error: "Only PDF and Word files are allowed" }, { status: 400 });
  }

  if (file.size > 5 * 1024 * 1024) {
    return NextResponse.json({ error: "File must be under 5MB" }, { status: 400 });
  }

  const bytes = await file.arrayBuffer();
  const path = `${userId}/${Date.now()}-${file.name}`;

  const { error: uploadError } = await supabaseAdmin().storage
    .from("resumes")
    .upload(path, bytes, { contentType: file.type, upsert: true });

  if (uploadError) {
    console.error("[resume upload] Storage error:", uploadError);
    return NextResponse.json({ error: "Could not upload resume" }, { status: 500 });
  }

  // Record in DB
  const { error: recordError } = await supabaseAdmin().from("resumes").upsert({
    user_id: userId,
    file_path: path,
    file_name: file.name,
    uploaded_at: new Date().toISOString(),
  });

  if (recordError) {
    console.error("[resume upload] DB error:", recordError);
    return NextResponse.json({ error: "Could not save resume" }, { status: 500 });
  }

  return NextResponse.json({ ok: true, path });
}
