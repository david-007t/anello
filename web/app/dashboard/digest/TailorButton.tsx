"use client";
import { useState } from "react";

export default function TailorButton({ jobId }: { jobId: string }) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");

  async function handleClick() {
    setState("loading");
    try {
      const res = await fetch("/api/tailor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      });
      if (!res.ok) throw new Error(await res.text());
      const { url } = await res.json();
      window.open(url, "_blank");
      setState("done");
    } catch {
      setState("error");
    } finally {
      setTimeout(() => setState("idle"), 3000);
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={state === "loading"}
      className="mt-2 text-xs font-medium px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 hover:bg-indigo-100 disabled:opacity-50 transition-colors whitespace-nowrap"
    >
      {state === "loading" ? "Tailoring…" : state === "done" ? "Opened ✓" : state === "error" ? "Failed" : "Tailor Resume"}
    </button>
  );
}
