import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

const PIPELINE_URL = process.env.PIPELINE_URL ?? "";
const OWNER_ID = "user_3BiDX7oXc0OkkXgLwwCIWK4VMu0";
const RESUME_LIMIT = 3;

export async function POST(req: Request) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  if (!PIPELINE_URL) {
    return NextResponse.json({ error: "PIPELINE_URL not configured" }, { status: 500 });
  }

  const { job_id, job_number } = await req.json();
  if (!job_id) return NextResponse.json({ error: "job_id required" }, { status: 400 });

  // Storage limit check (skip for owner)
  if (userId !== OWNER_ID) {
    const { data: files } = await supabaseAdmin().storage.from("tailored-resumes").list(userId);
    const resumeCount = (files ?? []).filter((f) => !f.name.endsWith("-cover-letter.pdf")).length;
    if (resumeCount >= RESUME_LIMIT) {
      return NextResponse.json(
        { error: "Resume limit reached (3 max). Delete a saved resume to continue." },
        { status: 403 }
      );
    }
  }

  const res = await fetch(`${PIPELINE_URL}/tailor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id, user_id: userId, job_number: job_number ?? 0 }),
  });

  if (!res.ok) {
    const err = await res.text();
    return NextResponse.json({ error: err }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
