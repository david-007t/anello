import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";
import { enforceSameOrigin } from "@/lib/api-security";
import { countRecentRequests, logRequest } from "@/lib/request-limits";

const PIPELINE_URL = process.env.PIPELINE_URL ?? "";
const DAILY_RUN_LIMIT = 3;

export async function POST(req: NextRequest) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const originError = enforceSameOrigin(req);
  if (originError) return originError;

  if (!PIPELINE_URL) {
    return NextResponse.json({ error: "PIPELINE_URL not configured" }, { status: 500 });
  }

  try {
    const sinceIso = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    const recentRuns = await countRecentRequests({
      action: "run_digest",
      userId,
      sinceIso,
    });

    if (recentRuns >= DAILY_RUN_LIMIT) {
      return NextResponse.json(
        { error: "You’ve already run your digest 3 times today. Come back tomorrow." },
        { status: 429 }
      );
    }
  } catch (error) {
    console.error("[run-digest] rate limit check failed:", error);
  }

  const runningRes = await fetch(`${PIPELINE_URL}/status?user_id=${encodeURIComponent(userId)}`, {
    cache: "no-store",
  });
  if (runningRes.ok) {
    const runningData = await runningRes.json();
    if (runningData.status === "running") {
      return NextResponse.json({ status: "already_running" });
    }
  }

  const res = await fetch(`${PIPELINE_URL}/run-user`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });

  if (!res.ok) {
    const err = await res.text();
    console.error("[run-digest] pipeline error:", err);
    return NextResponse.json({ error: "Could not start digest" }, { status: res.status });
  }

  const data = await res.json();
  if (data.status === "started") {
    try {
      await logRequest({
        action: "run_digest",
        userId,
        metadata: { source: "manual" },
      });
    } catch (error) {
      console.error("[run-digest] request log failed:", error);
    }
  }

  return NextResponse.json(data);
}
