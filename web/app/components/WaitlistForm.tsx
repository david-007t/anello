"use client";

import { useState, useRef, MouseEvent } from "react";

export default function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const btnRef = useRef<HTMLButtonElement>(null);
  const [glowPos, setGlowPos] = useState({ x: 50, y: 50 });
  const [hovered, setHovered] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    setStatus("loading");
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus("success");
        setMessage("You're on the list. We'll reach out when we launch.");
        setEmail("");
      } else {
        setStatus("error");
        setMessage(data.error || "Something went wrong. Try again.");
      }
    } catch {
      setStatus("error");
      setMessage("Something went wrong. Try again.");
    }
  }

  function handleMouseMove(e: MouseEvent<HTMLButtonElement>) {
    if (btnRef.current) {
      const rect = btnRef.current.getBoundingClientRect();
      setGlowPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
    }
  }

  if (status === "success") {
    return (
      <div className="flex items-center gap-3 border border-white/10 bg-white/5 backdrop-blur-sm rounded-xl px-5 py-4 max-w-md">
        <svg className="w-5 h-5 text-white/70 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        <p className="text-sm text-white/80 font-medium">{message}</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md">
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your email"
          required
          className="flex-1 px-4 py-3 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm text-white placeholder-white/30 text-sm focus:outline-none focus:border-white/30 transition"
        />
        <button
          ref={btnRef}
          type="submit"
          disabled={status === "loading"}
          onMouseMove={handleMouseMove}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          className="relative px-6 py-3 border border-white/10 bg-white/5 backdrop-blur-sm text-white/80 font-semibold text-sm rounded-xl overflow-hidden transition whitespace-nowrap cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          style={{ color: hovered ? '#ffffff' : undefined }}
        >
          <div
            className={`absolute w-[160px] h-[160px] rounded-full pointer-events-none -translate-x-1/2 -translate-y-1/2 transition-all duration-300 ${hovered ? 'opacity-25 scale-100' : 'opacity-0 scale-0'}`}
            style={{
              left: glowPos.x,
              top: glowPos.y,
              background: 'radial-gradient(circle, #9ca3af 10%, transparent 70%)',
            }}
          />
          <span className="relative z-10">{status === "loading" ? "Joining…" : "Join Waitlist"}</span>
        </button>
      </form>
      {status === "error" && (
        <p className="mt-2 text-sm text-red-400">{message}</p>
      )}
      <p className="mt-3 text-xs text-white/30">
        Free trial · No credit card required · Unsubscribe anytime
      </p>
    </div>
  );
}
