import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

export async function GET() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const supabase = supabaseAdmin();
  const { data: files, error } = await supabase.storage.from("tailored-resumes").list(userId);
  if (error || !files || files.length === 0) return NextResponse.json({ resumes: [] });

  const resumes = await Promise.all(
    files.map(async (f) => {
      const { data: signed } = await supabase.storage
        .from("tailored-resumes")
        .createSignedUrl(`${userId}/${f.name}`, 3600);
      return { name: f.name, url: signed?.signedUrl ?? null, created_at: f.created_at };
    })
  );

  return NextResponse.json({ resumes });
}

export async function DELETE(req: Request) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { name } = await req.json();
  if (!name || typeof name !== "string") {
    return NextResponse.json({ error: "name required" }, { status: 400 });
  }

  // Build and verify the full path server-side
  const path = `${userId}/${name}`;
  if (!path.startsWith(`${userId}/`)) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const supabase = supabaseAdmin();
  const { error } = await supabase.storage.from("tailored-resumes").remove([path]);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({ ok: true });
}
