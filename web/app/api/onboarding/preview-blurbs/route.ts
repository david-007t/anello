import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";
import { enforceSameOrigin } from "@/lib/api-security";

const PIPELINE_URL = process.env.PIPELINE_URL ?? "";

export async function POST(req: NextRequest) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const originError = enforceSameOrigin(req);
  if (originError) return originError;

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
    console.error("[preview-blurbs] pipeline error:", err);
    return NextResponse.json({ error: "Could not generate preview" }, { status: res.status });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
