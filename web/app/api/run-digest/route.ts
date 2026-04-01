import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const PIPELINE_URL = process.env.PIPELINE_URL ?? "";

export async function POST() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  if (!PIPELINE_URL) {
    return NextResponse.json({ error: "PIPELINE_URL not configured" }, { status: 500 });
  }

  const res = await fetch(`${PIPELINE_URL}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const err = await res.text();
    return NextResponse.json({ error: err }, { status: res.status });
  }

  return NextResponse.json({ status: "complete" });
}
