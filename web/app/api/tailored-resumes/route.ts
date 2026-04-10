import { auth } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";
export async function GET() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  return NextResponse.json({ resumes: [], cover_letters: [] });
}

export async function DELETE() {
  const { userId } = await auth();
  if (!userId) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  return NextResponse.json(
    { error: "Tailored resume downloads are disabled during early access." },
    { status: 403 }
  );
}
