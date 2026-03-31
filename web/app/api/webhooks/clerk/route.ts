import { NextRequest, NextResponse } from "next/server";
import { Webhook } from "svix";
import { supabaseAdmin } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  const secret = process.env.CLERK_WEBHOOK_SECRET;
  if (!secret) {
    console.error("CLERK_WEBHOOK_SECRET not set");
    return NextResponse.json({ error: "Misconfigured" }, { status: 500 });
  }

  // Verify svix signature
  const svixId = req.headers.get("svix-id");
  const svixTimestamp = req.headers.get("svix-timestamp");
  const svixSignature = req.headers.get("svix-signature");

  if (!svixId || !svixTimestamp || !svixSignature) {
    return NextResponse.json({ error: "Missing svix headers" }, { status: 400 });
  }

  const body = await req.text();
  const wh = new Webhook(secret);

  let payload: { type: string; data: Record<string, unknown> };
  try {
    payload = wh.verify(body, {
      "svix-id": svixId,
      "svix-timestamp": svixTimestamp,
      "svix-signature": svixSignature,
    }) as typeof payload;
  } catch (err) {
    console.error("Webhook signature verification failed:", err);
    return NextResponse.json({ error: "Invalid signature" }, { status: 401 });
  }

  const { type, data } = payload;
  const supabase = supabaseAdmin();

  try {
    if (type === "user.created") {
      const emailAddresses = data.email_addresses as Array<{ email_address: string }> | undefined;
      const email = emailAddresses?.[0]?.email_address ?? "";
      const { error } = await supabase.from("users").upsert({
        id: data.id,
        email,
        first_name: (data.first_name as string) ?? null,
        last_name: (data.last_name as string) ?? null,
        created_at: new Date().toISOString(),
      });
      if (error) {
        console.error("Supabase upsert error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
      }
    }

    if (type === "user.updated") {
      const emailAddresses = data.email_addresses as Array<{ email_address: string }> | undefined;
      const email = emailAddresses?.[0]?.email_address ?? "";
      await supabase.from("users").update({
        email,
        first_name: (data.first_name as string) ?? null,
        last_name: (data.last_name as string) ?? null,
      }).eq("id", data.id as string);
    }

    if (type === "user.deleted") {
      await supabase.from("users").delete().eq("id", data.id as string);
    }

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("Clerk webhook error:", err);
    return NextResponse.json({ error: "Internal error" }, { status: 500 });
  }
}
