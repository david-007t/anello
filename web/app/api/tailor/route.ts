import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";
import { enforceSameOrigin } from "@/lib/api-security";

export async function POST(req: NextRequest) {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const originError = enforceSameOrigin(req);
  if (originError) return originError;

  return NextResponse.json(
    { error: "Resume tailoring is disabled during early access." },
    { status: 403 }
  );
}
