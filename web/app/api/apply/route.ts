import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const PIPELINE_URL = process.env.PIPELINE_URL ?? "";

export async function POST(req: Request) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  if (!PIPELINE_URL) {
    return NextResponse.json({ error: "PIPELINE_URL not configured" }, { status: 500 });
  }

  const { job_id } = await req.json();
  if (!job_id) return NextResponse.json({ error: "job_id required" }, { status: 400 });

  const res = await fetch(`${PIPELINE_URL}/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id, user_id: userId }),
  });

  if (!res.ok) {
    const err = await res.text();
    return NextResponse.json({ error: err }, { status: res.status });
  }

  return NextResponse.json(await res.json());
}
