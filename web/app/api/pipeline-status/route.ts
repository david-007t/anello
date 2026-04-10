import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const PIPELINE_URL = process.env.PIPELINE_URL ?? "";

export async function GET() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  if (!PIPELINE_URL) {
    return NextResponse.json({ status: "idle", step: "", started_at: null, finished_at: null, error: null });
  }

  const res = await fetch(`${PIPELINE_URL}/status?user_id=${encodeURIComponent(userId)}`, { cache: "no-store" });
  if (!res.ok) {
    return NextResponse.json({ status: "idle", step: "", started_at: null, finished_at: null, error: null });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
