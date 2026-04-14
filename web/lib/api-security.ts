import { NextRequest, NextResponse } from "next/server";

const TAG_RE = /<[^>]*>/g;
const WHITESPACE_RE = /\s+/g;

export function getClientIp(req: NextRequest): string {
  const forwardedFor = req.headers.get("x-forwarded-for") ?? "";
  return forwardedFor.split(",")[0]?.trim() || "unknown";
}

export function enforceSameOrigin(req: NextRequest): NextResponse | null {
  const origin = req.headers.get("origin");
  const referer = req.headers.get("referer");
  const expectedOrigin = req.nextUrl.origin;

  if (origin) {
    if (origin !== expectedOrigin) {
      return NextResponse.json({ error: "Invalid origin" }, { status: 403 });
    }
    return null;
  }

  if (referer) {
    try {
      if (new URL(referer).origin !== expectedOrigin) {
        return NextResponse.json({ error: "Invalid origin" }, { status: 403 });
      }
      return null;
    } catch {
      return NextResponse.json({ error: "Invalid origin" }, { status: 403 });
    }
  }

  return NextResponse.json({ error: "Missing origin" }, { status: 403 });
}

export function sanitizeText(value: unknown, maxLength = 500): string | undefined {
  if (typeof value !== "string") return undefined;

  const cleaned = value
    .replace(TAG_RE, " ")
    .replace(WHITESPACE_RE, " ")
    .trim()
    .slice(0, maxLength);

  return cleaned;
}
