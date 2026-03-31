import { NextRequest, NextResponse } from "next/server";
import { supabaseAdmin } from "@/lib/supabase";

// Clerk sends a svix-signature header — verify it in production
// Add CLERK_WEBHOOK_SECRET to Vercel env vars after creating the webhook in Clerk dashboard
// Clerk dashboard → Webhooks → Add endpoint → https://anelo.io/api/webhooks/clerk
// Events to subscribe: user.created, user.updated, user.deleted

export async function POST(req: NextRequest) {
  try {
    const payload = await req.json();
    const { type, data } = payload;

    const supabase = supabaseAdmin();

    if (type === "user.created") {
      const email = data.email_addresses?.[0]?.email_address ?? "";
      const { error } = await supabase.from("users").upsert({
        id: data.id,
        email,
        first_name: data.first_name ?? null,
        last_name: data.last_name ?? null,
        created_at: new Date().toISOString(),
      });

      if (error) {
        console.error("Supabase upsert error:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
      }
    }

    if (type === "user.updated") {
      const email = data.email_addresses?.[0]?.email_address ?? "";
      await supabase.from("users").update({
        email,
        first_name: data.first_name ?? null,
        last_name: data.last_name ?? null,
      }).eq("id", data.id);
    }

    if (type === "user.deleted") {
      await supabase.from("users").delete().eq("id", data.id);
    }

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("Clerk webhook error:", err);
    return NextResponse.json({ error: "Internal error" }, { status: 500 });
  }
}
