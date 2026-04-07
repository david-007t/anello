import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const PIPELINE_URL = process.env.PIPELINE_URL ?? "";

export async function POST(req: Request) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  if (!PIPELINE_URL) {
    return NextResponse.json({ error: "PIPELINE_URL not configured" }, { status: 500 });
  }

  const body = await req.json();

  const res = await fetch(`${PIPELINE_URL}/preview-blurbs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    return NextResponse.json({ error: err }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
