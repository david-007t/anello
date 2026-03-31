import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const { email } = await req.json();

    if (!email || typeof email !== "string" || !email.includes("@")) {
      return NextResponse.json({ error: "Valid email required." }, { status: 400 });
    }

    const normalizedEmail = email.trim().toLowerCase();

    // --- Resend integration ---
    // Set RESEND_API_KEY in your Vercel environment variables.
    // Optionally set RESEND_AUDIENCE_ID to add contacts to an audience.
    const resendKey = process.env.RESEND_API_KEY;

    if (resendKey) {
      const audienceId = process.env.RESEND_AUDIENCE_ID;

      if (audienceId) {
        // Add to Resend audience
        const res = await fetch(
          `https://api.resend.com/audiences/${audienceId}/contacts`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${resendKey}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              email: normalizedEmail,
              unsubscribed: false,
            }),
          }
        );

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          console.error("Resend audience error:", err);
          // Don't fail the user — log and continue
        }
      }

      // Send notification email to the owner
      const ownerEmail = process.env.WAITLIST_NOTIFY_EMAIL;
      if (ownerEmail) {
        await fetch("https://api.resend.com/emails", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${resendKey}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            from: "Anello Waitlist <waitlist@anello.io>",
            to: [ownerEmail],
            subject: `New waitlist signup: ${normalizedEmail}`,
            text: `${normalizedEmail} just joined the Anello waitlist.`,
          }),
        });
      }
    } else {
      // No Resend key — log to server console for local dev
      console.log(`[waitlist] New signup: ${normalizedEmail}`);
    }

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("Waitlist error:", err);
    return NextResponse.json({ error: "Internal server error." }, { status: 500 });
  }
}
